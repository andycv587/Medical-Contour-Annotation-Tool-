import importlib
import os
import time
from typing import Any, Dict, Optional, Sequence

import numpy as np
from PIL import Image

from .base import (
    BackendStatus,
    SegmentationBackend,
    SegmentationResult,
    ensure_uint8,
    now_runtime,
    prompt_type,
    run_external_npy_bridge,
)


class LangSAMBackend(SegmentationBackend):
    name = "langsam"
    version = "bridge/direct"
    supports_2d = True
    supports_3d = False
    supports_text_prompt = True
    supports_bbox_prompt = False
    supports_points = False
    supports_microscopy = True
    supports_medical_volume = False

    def check_available(self) -> BackendStatus:
        cmd = os.environ.get("LANGSAM_INFER_CMD", "").strip()
        if cmd:
            return BackendStatus(True, "LANGSAM_INFER_CMD configured", self.version, None, {"mode": "external", "cmd": cmd})
        try:
            mod = importlib.import_module("lang_sam")
            ver = getattr(mod, "__version__", None)
            return BackendStatus(True, "lang_sam import available", ver, _detect_torch_device(), {"mode": "direct"})
        except Exception as ex:
            return BackendStatus(False, f"LangSAM unavailable: {ex}", None, None, {"env": "LANGSAM_INFER_CMD"})

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
        cfg = dict(config or {})
        if not prompt:
            raise ValueError("LangSAM requires a text prompt")
        start = time.perf_counter()
        arr = ensure_uint8(image)
        if arr.ndim != 2:
            raise ValueError(f"LangSAM backend expects 2D image, got {arr.shape}")
        cmd = cfg.get("cmd") or os.environ.get("LANGSAM_INFER_CMD", "").strip()
        warnings = []
        metadata: Dict[str, Any] = {}
        if cmd:
            mask, bridge_warnings, bridge_meta = run_external_npy_bridge(
                cmd=cmd,
                image=arr,
                request={"prompt": prompt, **cfg},
                timeout_sec=int(cfg.get("timeout_sec", 180)),
                volume_mode=False,
            )
            warnings.extend(bridge_warnings)
            metadata.update(bridge_meta)
            if mask is None:
                raise RuntimeError("; ".join(bridge_warnings) or "LangSAM external bridge failed")
            if mask.ndim == 3:
                mask = np.max(mask > 0, axis=0).astype(np.uint8)
            else:
                mask = (mask > 0).astype(np.uint8)
        else:
            mask, metadata = self._direct_predict(arr, prompt)
        return SegmentationResult(mask, None, self.name, self.version, prompt_type(prompt, None, None), now_runtime(start), metadata, warnings)

    def _direct_predict(self, arr: np.ndarray, prompt: str):
        mod = importlib.import_module("lang_sam")
        langsam_cls = getattr(mod, "LangSAM")
        model = langsam_cls()
        pil = Image.fromarray(np.stack([arr] * 3, axis=-1), mode="RGB")
        try:
            result = model.predict([pil], [prompt])
        except Exception:
            result = model.predict(pil, prompt)
        masks = []
        if isinstance(result, dict) and "masks" in result:
            masks = result["masks"]
        elif isinstance(result, (list, tuple)):
            if result and isinstance(result[0], dict):
                for item in result:
                    masks.extend(item.get("masks", []))
            elif result:
                masks = result[0] if isinstance(result[0], (list, tuple, np.ndarray)) else result
        merged = np.zeros_like(arr, dtype=np.uint8)
        for m in masks:
            ma = np.asarray(m)
            if ma.ndim > 2:
                ma = ma[..., 0]
            if ma.shape == arr.shape:
                merged = np.maximum(merged, (ma > 0).astype(np.uint8))
        return merged, {"mode": "direct", "raw_mask_count": len(masks)}


def _detect_torch_device() -> Optional[str]:
    try:
        torch = importlib.import_module("torch")
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return None
