import importlib
import os
import time
from typing import Any, Dict, Optional, Sequence

import numpy as np

from .base import BackendStatus, SegmentationBackend, SegmentationResult, ensure_uint8, now_runtime, prompt_type, run_external_npy_bridge


class MedSAM2Backend(SegmentationBackend):
    name = "medsam2"
    version = "bridge"
    supports_2d = True
    supports_3d = True
    supports_text_prompt = False
    supports_bbox_prompt = True
    supports_points = False
    supports_microscopy = False
    supports_medical_volume = True

    def check_available(self) -> BackendStatus:
        cmd = os.environ.get("MEDSAM2_INFER_CMD", "").strip()
        if cmd:
            return BackendStatus(True, "MEDSAM2_INFER_CMD configured", self.version, _detect_torch_device(), {"mode": "external", "cmd": cmd})
        try:
            mod = importlib.import_module("sam2")
            return BackendStatus(False, "MedSAM2/SAM2 import detected but direct adapter is not implemented; configure MEDSAM2_INFER_CMD with a real upstream adapter", getattr(mod, "__version__", None), _detect_torch_device(), {"mode": "direct-unimplemented", "module": "sam2"})
        except Exception as ex:
            return BackendStatus(False, f"MedSAM2 unavailable: {ex}", None, None, {"env": "MEDSAM2_INFER_CMD"})

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
        volume_mode = arr.ndim == 3
        if arr.ndim == 2:
            arr_for_bridge = arr[np.newaxis, ...]
            volume_mode = True
        elif arr.ndim == 3:
            arr_for_bridge = arr
        else:
            raise ValueError(f"MedSAM2 backend expects 2D or 3D image, got {arr.shape}")
        cmd = cfg.get("cmd") or os.environ.get("MEDSAM2_INFER_CMD", "").strip()
        warnings = []
        metadata = {"checkpoint_path": cfg.get("checkpoint_path"), "device": cfg.get("device")}
        if not cmd:
            warnings.append("MEDSAM2_INFER_CMD is not configured; returning empty mask")
            mask = np.zeros_like(arr_for_bridge, dtype=np.uint8)
        else:
            request = {"prompt": prompt or "", "bbox": bbox, **cfg}
            mask, bridge_warnings, bridge_meta = run_external_npy_bridge(
                cmd=cmd,
                image=arr_for_bridge,
                request=request,
                timeout_sec=int(cfg.get("timeout_sec", 600)),
                volume_mode=volume_mode,
            )
            warnings.extend(bridge_warnings)
            metadata.update(bridge_meta)
            if mask is None:
                raise RuntimeError("; ".join(bridge_warnings) or "MedSAM2 external bridge failed")
            mask = (mask > 0).astype(np.uint8)
        if np.asarray(image).ndim == 2 and mask.ndim == 3:
            mask = mask[0]
        return SegmentationResult(mask, None, self.name, self.version, prompt_type(prompt, bbox, None), now_runtime(start), metadata, warnings)


def _detect_torch_device() -> Optional[str]:
    try:
        torch = importlib.import_module("torch")
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return None
