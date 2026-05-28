import hashlib
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def image_fingerprint(image=None, path: str = "") -> str:
    h = hashlib.sha256()
    if path:
        h.update(os.path.basename(path).encode("utf-8"))
    if image is not None:
        arr = np.asarray(image)
        h.update(str(tuple(arr.shape)).encode("utf-8"))
        h.update(str(arr.dtype).encode("utf-8"))
        if arr.size:
            safe = np.nan_to_num(arr.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
            stats = np.array([safe.min(), safe.max(), safe.mean(), safe.std()], dtype=np.float32)
            h.update(stats.tobytes())
            sample = safe.ravel()[:: max(1, safe.size // 2048)]
            h.update(np.ascontiguousarray(sample).tobytes())
    return h.hexdigest()[:32]


@dataclass
class MemoryEvent:
    image_fingerprint: str
    image_shape: List[int]
    modality_guess: str
    prompt_type: str
    selected_backend: str
    backend_version: str
    timestamp: str = field(default_factory=utc_now)
    text_prompt: Optional[str] = None
    bbox: Optional[List[int]] = None
    points: Optional[List[List[float]]] = None
    seed_summary: Optional[Dict[str, Any]] = None
    model_checkpoint_id: Optional[str] = None
    segmentation_parameters: Dict[str, Any] = field(default_factory=dict)
    mask_summary_statistics: Dict[str, Any] = field(default_factory=dict)
    runtime_sec: Optional[float] = None
    correction_count: Optional[int] = None
    dice: Optional[float] = None
    iou: Optional[float] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    provenance_id: Optional[str] = None
    raw_image_saved: bool = False
    raw_image: Optional[Any] = None

    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        data = asdict(self)
        if not include_raw:
            data.pop("raw_image", None)
            data["raw_image_saved"] = False
        return _json_safe(data)


def mask_summary(mask) -> Dict[str, Any]:
    if mask is None:
        return {}
    arr = np.asarray(mask)
    return {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "nonzero": int(np.count_nonzero(arr)),
        "unique_count": int(np.unique(arr).size) if arr.size <= 10_000_000 else None,
    }


def _json_safe(value):
    if isinstance(value, np.ndarray):
        return {"ndarray_shape": list(value.shape), "dtype": str(value.dtype), "nonzero": int(np.count_nonzero(value))}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value
