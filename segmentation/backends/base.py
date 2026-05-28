import abc
import json
import os
import shlex
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


@dataclass
class BackendStatus:
    available: bool
    reason: str
    detected_version: Optional[str] = None
    device: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SegmentationResult:
    mask: np.ndarray
    confidence: Optional[float]
    backend_name: str
    backend_version: str
    prompt_type: str
    runtime_sec: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_summary(self) -> Dict[str, Any]:
        arr = np.asarray(self.mask)
        return {
            "mask_shape": list(arr.shape),
            "mask_dtype": str(arr.dtype),
            "mask_nonzero": int(np.count_nonzero(arr)),
            "confidence": self.confidence,
            "backend_name": self.backend_name,
            "backend_version": self.backend_version,
            "prompt_type": self.prompt_type,
            "runtime_sec": self.runtime_sec,
            "metadata": json_safe(self.metadata),
            "warnings": list(self.warnings),
        }


class SegmentationBackend(abc.ABC):
    name: str = "base"
    version: str = "0.1.0"
    supports_2d: bool = False
    supports_3d: bool = False
    supports_text_prompt: bool = False
    supports_bbox_prompt: bool = False
    supports_points: bool = False
    supports_microscopy: bool = False
    supports_medical_volume: bool = False

    @abc.abstractmethod
    def check_available(self) -> BackendStatus:
        raise NotImplementedError

    @abc.abstractmethod
    def segment(
        self,
        image,
        prompt: Optional[str] = None,
        bbox: Optional[Sequence[int]] = None,
        points: Optional[Sequence[Sequence[float]]] = None,
        labels: Optional[Sequence[int]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SegmentationResult:
        raise NotImplementedError


def prompt_type(prompt=None, bbox=None, points=None) -> str:
    kinds = []
    if prompt:
        kinds.append("text")
    if bbox is not None:
        kinds.append("bbox")
    if points is not None:
        kinds.append("points")
    return "+".join(kinds) if kinds else "none"


def now_runtime(start: float) -> float:
    return float(time.perf_counter() - start)


def json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return {
            "ndarray_shape": list(value.shape),
            "dtype": str(value.dtype),
            "nonzero": int(np.count_nonzero(value)),
        }
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def ensure_uint8(image) -> np.ndarray:
    arr = np.asarray(image)
    arr = np.nan_to_num(arr, nan=0.0, posinf=255.0, neginf=0.0)
    if arr.dtype == np.uint8:
        return arr
    arr = arr.astype(np.float32)
    lo = float(np.min(arr))
    hi = float(np.max(arr))
    if hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)
    return np.clip((arr - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def split_command(cmd: str) -> List[str]:
    try:
        parts = shlex.split(cmd, posix=False)
    except Exception:
        parts = cmd.split()
    cleaned = []
    for part in parts:
        p = str(part).strip()
        if len(p) >= 2 and ((p[0] == p[-1] == '"') or (p[0] == p[-1] == "'")):
            p = p[1:-1]
        if p:
            cleaned.append(p)
    return cleaned


def run_external_npy_bridge(
    *,
    cmd: str,
    image: np.ndarray,
    request: Dict[str, Any],
    timeout_sec: int,
    volume_mode: bool = False,
) -> tuple[Optional[np.ndarray], List[str], Dict[str, Any]]:
    warnings: List[str] = []
    metadata: Dict[str, Any] = {"bridge_cmd": cmd, "volume_mode": volume_mode}
    with tempfile.TemporaryDirectory(prefix="seg_backend_bridge_") as tmp_dir:
        in_name = "input_volume.npy" if volume_mode else "input.npy"
        out_name = "output_volume.npy" if volume_mode else "output.npy"
        input_npy = os.path.join(tmp_dir, in_name)
        request_json = os.path.join(tmp_dir, "request.json")
        output_npy = os.path.join(tmp_dir, out_name)
        np.save(input_npy, np.asarray(image).astype(np.uint8))

        payload = {}
        for key, value in dict(request or {}).items():
            if isinstance(value, np.ndarray):
                value_path = os.path.join(tmp_dir, f"{key}.npy")
                np.save(value_path, value.astype(np.uint8))
                payload[f"{key}_path"] = value_path
            else:
                payload[key] = json_safe(value)
        with open(request_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        cmd_parts = split_command(cmd)
        if not cmd_parts:
            return None, ["external command is empty"], metadata
        args = cmd_parts
        if volume_mode:
            args = args + ["--mode", "volume"]
        args = args + ["--input", input_npy, "--request", request_json, "--output", output_npy]
        completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout_sec)
        metadata["returncode"] = completed.returncode
        metadata["stdout"] = (completed.stdout or "").strip()
        metadata["stderr"] = (completed.stderr or "").strip()
        if completed.returncode != 0:
            warnings.append(metadata["stderr"] or metadata["stdout"] or f"bridge failed with code {completed.returncode}")
            return None, warnings, metadata
        if not os.path.exists(output_npy):
            warnings.append("external bridge did not produce output file")
            return None, warnings, metadata
        return np.load(output_npy), warnings, metadata
