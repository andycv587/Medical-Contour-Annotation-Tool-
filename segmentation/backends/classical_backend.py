import time
from typing import Any, Dict, Optional, Sequence

import cv2
import numpy as np

from .base import BackendStatus, SegmentationBackend, SegmentationResult, ensure_uint8, now_runtime, prompt_type


class ClassicalBackend(SegmentationBackend):
    name = "classical"
    version = "0.1.0"
    supports_2d = True
    supports_3d = True
    supports_text_prompt = False
    supports_bbox_prompt = True
    supports_points = False
    supports_microscopy = True
    supports_medical_volume = True

    def check_available(self) -> BackendStatus:
        return BackendStatus(True, "OpenCV classical baselines available", self.version, None, {"opencv": cv2.__version__})

    def segment(
        self,
        image,
        prompt: Optional[str] = None,
        bbox: Optional[Sequence[int]] = None,
        points: Optional[Sequence[Sequence[float]]] = None,
        labels: Optional[Sequence[int]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SegmentationResult:
        _ = labels
        start = time.perf_counter()
        cfg = dict(config or {})
        arr = ensure_uint8(image)
        method = str(cfg.get("method", "watershed")).lower()
        if arr.ndim == 2:
            mask = _segment_2d(arr, method, bbox, cfg)
        elif arr.ndim == 3:
            mask = np.stack([_segment_2d(sl, method, bbox, cfg) for sl in arr], axis=0).astype(np.uint8)
        else:
            raise ValueError(f"classical backend expects 2D or 3D image, got {arr.shape}")
        return SegmentationResult(
            mask=mask,
            confidence=None,
            backend_name=self.name,
            backend_version=self.version,
            prompt_type=prompt_type(prompt, bbox, points),
            runtime_sec=now_runtime(start),
            metadata={"method": method, "parameters": cfg},
            warnings=[],
        )


def _segment_2d(image_u8: np.ndarray, method: str, bbox, cfg: Dict[str, Any]) -> np.ndarray:
    if method == "levelset":
        return _levelset_like(image_u8, cfg)
    if method == "cellseg":
        return _cell_like(image_u8, cfg)
    return _watershed_like(image_u8, bbox, cfg)


def _watershed_like(image_u8: np.ndarray, bbox, cfg: Dict[str, Any]) -> np.ndarray:
    work = image_u8.copy()
    roi = None
    if bbox is not None:
        roi = np.zeros_like(work, dtype=np.uint8)
        x1, y1, x2, y2 = _sanitize_bbox(bbox, work.shape)
        roi[y1 : y2 + 1, x1 : x2 + 1] = 1
    blur = cv2.GaussianBlur(work, (5, 5), 0)
    percentile = float(cfg.get("percentile", 65))
    if roi is not None and np.any(roi):
        vals = blur[roi > 0]
        thr = np.percentile(vals, percentile) if vals.size else np.percentile(blur, percentile)
    else:
        thr = np.percentile(blur, percentile)
    mask = (blur >= thr).astype(np.uint8)
    if roi is not None:
        mask = mask * roi
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask * 255, cv2.MORPH_OPEN, kernel, iterations=int(cfg.get("open_iters", 1)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=int(cfg.get("close_iters", 1)))
    return (mask > 0).astype(np.uint8)


def _levelset_like(image_u8: np.ndarray, cfg: Dict[str, Any]) -> np.ndarray:
    f = cv2.GaussianBlur(image_u8, (5, 5), 0).astype(np.float32) / 255.0
    mask = f > float(np.mean(f))
    iterations = max(1, int(cfg.get("iterations", 20)))
    k = int(cfg.get("kernel_size", 3))
    if k % 2 == 0:
        k += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    for _ in range(iterations):
        fg = f[mask]
        bg = f[~mask]
        if fg.size == 0 or bg.size == 0:
            break
        c1 = float(np.mean(fg))
        c0 = float(np.mean(bg))
        new_mask = (f - c1) ** 2 < (f - c0) ** 2
        m = cv2.morphologyEx(new_mask.astype(np.uint8) * 255, cv2.MORPH_OPEN, kernel)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
        mask = m > 0
    return mask.astype(np.uint8)


def _cell_like(image_u8: np.ndarray, cfg: Dict[str, Any]) -> np.ndarray:
    _ = cfg
    blur = cv2.GaussianBlur(image_u8, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    return (opened > 0).astype(np.uint8)


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
