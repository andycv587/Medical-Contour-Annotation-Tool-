import importlib
import os
import time
from typing import Any, Dict, Optional, Sequence

import cv2
import numpy as np

from .base import BackendStatus, SegmentationBackend, SegmentationResult, ensure_uint8, now_runtime, prompt_type, run_external_npy_bridge


class CellposeBackend(SegmentationBackend):
    name = "cellpose"
    version = "cellpose-or-opencv-fallback"
    supports_2d = True
    supports_3d = False
    supports_text_prompt = False
    supports_bbox_prompt = False
    supports_points = False
    supports_microscopy = True
    supports_medical_volume = False

    def check_available(self) -> BackendStatus:
        cmd = os.environ.get("CELLPOSE_INFER_CMD", "").strip()
        if cmd:
            return BackendStatus(True, "CELLPOSE_INFER_CMD configured", self.version, _detect_torch_device(), {"mode": "external", "cmd": cmd})
        try:
            cellpose = importlib.import_module("cellpose")
            ver = getattr(cellpose, "__version__", None)
            return BackendStatus(True, "cellpose import available", ver, _detect_torch_device(), {"mode": "cellpose"})
        except Exception as ex:
            return BackendStatus(True, f"cellpose unavailable ({ex}); OpenCV fallback available", self.version, None, {"mode": "opencv-fallback"})

    def segment(
        self,
        image,
        prompt: Optional[str] = None,
        bbox: Optional[Sequence[int]] = None,
        points: Optional[Sequence[Sequence[float]]] = None,
        labels: Optional[Sequence[int]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SegmentationResult:
        _ = bbox
        _ = points
        _ = labels
        start = time.perf_counter()
        cfg = dict(config or {})
        arr = ensure_uint8(image)
        if arr.ndim != 2:
            raise ValueError(f"Cellpose backend expects 2D image, got {arr.shape}")
        warnings = []
        metadata: Dict[str, Any] = {"parameters": cfg}
        cmd = cfg.get("cmd") or os.environ.get("CELLPOSE_INFER_CMD", "").strip()
        if cmd:
            mask, bridge_warnings, bridge_meta = run_external_npy_bridge(
                cmd=cmd,
                image=arr,
                request=cfg,
                timeout_sec=int(cfg.get("timeout_sec", 300)),
                volume_mode=False,
            )
            warnings.extend(bridge_warnings)
            metadata.update(bridge_meta)
            metadata["mode"] = "external"
            if mask is None:
                raise RuntimeError("; ".join(bridge_warnings) or "Cellpose external bridge failed")
        else:
            try:
                mask, meta = self._run_cellpose(arr, cfg)
                metadata.update(meta)
            except Exception as ex:
                warnings.append(f"Cellpose unavailable or failed; used OpenCV fallback: {ex}")
                mask = _opencv_cell_instances(arr, cfg)
                metadata["mode"] = "opencv-fallback"
        return SegmentationResult(mask.astype(np.uint16), None, self.name, self.version, prompt_type(prompt, None, None), now_runtime(start), metadata, warnings)

    def _run_cellpose(self, arr: np.ndarray, cfg: Dict[str, Any]):
        models = importlib.import_module("cellpose.models")
        model_type = cfg.get("model_type", "cyto")
        model = models.CellposeModel(gpu=bool(cfg.get("gpu", False)), model_type=model_type)
        channels = cfg.get("channels", [0, 0])
        masks, flows, styles = model.eval(
            arr,
            diameter=cfg.get("diameter"),
            channels=channels,
            flow_threshold=float(cfg.get("flow_threshold", 0.4)),
            cellprob_threshold=float(cfg.get("cellprob_threshold", 0.0)),
        )
        return np.asarray(masks), {"mode": "cellpose", "model_type": model_type, "channels": channels, "flows_present": flows is not None, "styles_present": styles is not None}


def _opencv_cell_instances(arr: np.ndarray, cfg: Dict[str, Any]) -> np.ndarray:
    min_area = int(cfg.get("min_cell_area", 20))
    max_area = int(cfg.get("max_cell_area", max(min_area + 1, arr.size // 3)))
    lo, hi = np.percentile(arr, [1, 99])
    if hi <= lo:
        hi = lo + 1
    norm = np.clip((arr.astype(np.float32) - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    work = clahe.apply(norm)
    blur = cv2.GaussianBlur(work, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    n, labels, stats, _ = cv2.connectedComponentsWithStats((binary > 0).astype(np.uint8), connectivity=8)
    out = np.zeros(arr.shape, dtype=np.uint16)
    next_id = 1
    for label in range(1, n):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if min_area <= area <= max_area:
            out[labels == label] = next_id
            next_id += 1
    return out


def _detect_torch_device() -> Optional[str]:
    try:
        torch = importlib.import_module("torch")
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return None
