import time
from typing import Any, Dict, Optional, Sequence

import numpy as np

from .base import BackendStatus, SegmentationBackend, SegmentationResult, ensure_uint8, now_runtime, prompt_type


class MockBackend(SegmentationBackend):
    name = "mock"
    version = "0.1.0"
    supports_2d = True
    supports_3d = True
    supports_text_prompt = True
    supports_bbox_prompt = True
    supports_points = True
    supports_microscopy = True
    supports_medical_volume = True

    def check_available(self) -> BackendStatus:
        return BackendStatus(True, "mock backend is always available", self.version, None, {"mode": "ci"})

    def segment(
        self,
        image,
        prompt: Optional[str] = None,
        bbox: Optional[Sequence[int]] = None,
        points: Optional[Sequence[Sequence[float]]] = None,
        labels: Optional[Sequence[int]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SegmentationResult:
        _ = points
        _ = labels
        _ = config
        start = time.perf_counter()
        arr = ensure_uint8(image)
        mask = np.zeros(arr.shape, dtype=np.uint8)
        if arr.ndim == 2:
            if bbox is not None:
                x1, y1, x2, y2 = _sanitize_bbox(bbox, arr.shape)
                mask[y1 : y2 + 1, x1 : x2 + 1] = 1
            else:
                mask = (arr >= np.percentile(arr, 70)).astype(np.uint8)
        elif arr.ndim == 3:
            if bbox is not None:
                x1, y1, x2, y2 = _sanitize_bbox(bbox, arr.shape[-2:])
                mask[:, y1 : y2 + 1, x1 : x2 + 1] = 1
            else:
                mask = (arr >= np.percentile(arr, 70)).astype(np.uint8)
        else:
            raise ValueError(f"mock backend expects 2D or 3D image, got {arr.shape}")
        return SegmentationResult(
            mask=mask.astype(np.uint8),
            confidence=None,
            backend_name=self.name,
            backend_version=self.version,
            prompt_type=prompt_type(prompt, bbox, points),
            runtime_sec=now_runtime(start),
            metadata={"mock": True},
            warnings=[],
        )


def _sanitize_bbox(bbox, shape):
    h, w = shape
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w - 1, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h - 1, y2))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return x1, y1, x2, y2
