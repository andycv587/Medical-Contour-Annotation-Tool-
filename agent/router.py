from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


CELL_TOKENS = (
    "cell",
    "cells",
    "nuclei",
    "nucleus",
    "dapi",
    "microscopy",
    "fluorescence",
    "histology",
    "brightfield",
    "phase",
    "cytoplasm",
)


@dataclass
class RoutingDecision:
    selected_backend: Optional[str]
    ranked_candidates: List[str]
    decision_reason: str
    fallback_history: List[Dict[str, Any]] = field(default_factory=list)
    unavailable_backends: Dict[str, str] = field(default_factory=dict)
    prompt_interpretation: Dict[str, Any] = field(default_factory=dict)
    image_type_guess: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgenticRouter:
    def __init__(self, preferred_order: Optional[List[str]] = None):
        self.preferred_order = preferred_order or ["medsam2", "medsam", "langsam", "cellpose", "classical", "mock"]

    def route(
        self,
        image,
        *,
        prompt: Optional[str] = None,
        bbox: Optional[Sequence[int]] = None,
        points=None,
        seed=None,
        metadata: Optional[Dict[str, Any]] = None,
        backend_statuses: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        metadata = metadata or {}
        statuses = backend_statuses or {}
        prompt_info = self.interpret_prompt(prompt)
        image_type = guess_image_type(image, metadata)
        has_seed = seed is not None and np.any(np.asarray(seed) > 0)
        ranked, reason = self.rank_candidates(image_type, prompt_info, bbox=bbox, points=points, has_seed=has_seed)
        unavailable = {}
        for name, status in statuses.items():
            available = bool(getattr(status, "available", status.get("available") if isinstance(status, dict) else False))
            if not available:
                unavailable[name] = getattr(status, "reason", status.get("reason", "") if isinstance(status, dict) else "")
        selected = next((name for name in ranked if name not in unavailable), ranked[0] if ranked else None)
        return RoutingDecision(
            selected_backend=selected,
            ranked_candidates=ranked,
            decision_reason=reason,
            fallback_history=[],
            unavailable_backends=unavailable,
            prompt_interpretation=prompt_info,
            image_type_guess=image_type,
        )

    def rank_candidates(self, image_type: str, prompt_info: Dict[str, Any], *, bbox=None, points=None, has_seed=False) -> tuple[List[str], str]:
        _ = points
        has_text = bool(prompt_info.get("text_prompt"))
        is_cell = bool(prompt_info.get("is_cell_task"))
        if image_type == "medical_volume" and (bbox is not None or has_seed):
            return ["medsam2", "medsam", "classical", "mock"], "3D medical volume with bbox/seed; prefer MedSAM2 propagation"
        if is_cell or image_type == "microscopy":
            return ["cellpose", "classical", "langsam", "mock"], "microscopy/cell prompt or metadata detected; prefer Cellpose/CellSeg"
        if image_type == "medical_2d" and bbox is not None:
            return ["medsam", "medsam2", "classical", "mock"], "2D medical image with bbox; prefer MedSAM"
        if has_text and image_type in ("biomedical_2d", "natural_or_2d", "unknown_2d", "medical_2d"):
            return ["langsam", "cellpose", "classical", "mock"], "2D image with text prompt; prefer LangSAM"
        if image_type == "medical_volume":
            return ["medsam2", "classical", "mock"], "3D volume without prompt; prefer MedSAM2 if available"
        return ["classical", "mock"], "no specialized prompt/backend signal; use classical fallback"

    @staticmethod
    def interpret_prompt(prompt: Optional[str]) -> Dict[str, Any]:
        text = (prompt or "").strip()
        lower = text.lower()
        matched = [tok for tok in CELL_TOKENS if tok in lower]
        return {
            "text_prompt": text,
            "has_text": bool(text),
            "is_cell_task": bool(matched),
            "matched_cell_tokens": matched,
        }


def guess_image_type(image, metadata: Optional[Dict[str, Any]] = None) -> str:
    metadata = metadata or {}
    modality = str(metadata.get("modality", "") or metadata.get("image_type", "")).lower()
    if any(tok in modality for tok in ("microscopy", "dapi", "fluorescence", "histology", "pathology")):
        return "microscopy"
    if any(tok in modality for tok in ("ct", "mr", "mri", "pet", "nifti", "medical")):
        arr = np.asarray(image)
        return "medical_volume" if arr.ndim == 3 and arr.shape[0] > 1 else "medical_2d"
    arr = np.asarray(image)
    if arr.ndim == 3 and arr.shape[0] > 1:
        return "medical_volume"
    if arr.ndim == 2:
        return "unknown_2d"
    return "unknown"
