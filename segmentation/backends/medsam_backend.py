import importlib
import os
import time
from typing import Any, Dict, Optional, Sequence

import numpy as np

from .base import BackendStatus, SegmentationBackend, SegmentationResult, ensure_uint8, now_runtime, prompt_type, run_external_npy_bridge


class MedSAMBackend(SegmentationBackend):
    name = "medsam"
    version = "bridge"
    supports_2d = True
    supports_3d = True
    supports_text_prompt = False
    supports_bbox_prompt = True
    supports_points = False
    supports_microscopy = False
    supports_medical_volume = True

    def check_available(self) -> BackendStatus:
        cmd = os.environ.get("MEDSAM_INFER_CMD", "").strip()
        if cmd:
            return BackendStatus(True, "MEDSAM_INFER_CMD configured", self.version, None, {"mode": "external", "cmd": cmd})
        try:
            mod = importlib.import_module("medsam")
            return BackendStatus(False, "medsam import detected but direct adapter is not implemented; configure MEDSAM_INFER_CMD", getattr(mod, "__version__", None), None, {"mode": "direct-unimplemented"})
        except Exception as ex:
            return BackendStatus(False, f"MedSAM unavailable: {ex}", None, None, {"env": "MEDSAM_INFER_CMD"})

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
        start = time.perf_counter()
        cfg = dict(config or {})
        arr = ensure_uint8(image)
        if arr.ndim not in (2, 3):
            raise ValueError(f"MedSAM backend expects 2D image or 3D volume, got {arr.shape}")
        cmd = cfg.get("cmd") or os.environ.get("MEDSAM_INFER_CMD", "").strip()
        warnings = []
        volume_mode = arr.ndim == 3
        metadata = {
            "checkpoint_path": cfg.get("checkpoint_path"),
            "mode": "slice_wise_volume" if volume_mode else "image",
        }
        if not cmd:
            warnings.append("MEDSAM_INFER_CMD is not configured; returning empty mask")
            mask = np.zeros_like(arr, dtype=np.uint8)
        else:
            request = {"prompt": prompt or "", "bbox": bbox, **cfg}
            mask, bridge_warnings, bridge_meta = run_external_npy_bridge(
                cmd=cmd,
                image=arr,
                request=request,
                timeout_sec=int(cfg.get("timeout_sec", 1800 if volume_mode else 180)),
                volume_mode=volume_mode,
            )
            warnings.extend(bridge_warnings)
            metadata.update(bridge_meta)
            if mask is None:
                raise RuntimeError("; ".join(bridge_warnings) or "MedSAM external bridge failed")
            if not volume_mode and mask.ndim == 3:
                mask = np.max(mask > 0, axis=0).astype(np.uint8)
            else:
                mask = (mask > 0).astype(np.uint8)
        return SegmentationResult(mask, None, self.name, self.version, prompt_type(prompt, bbox, None), now_runtime(start), metadata, warnings)
