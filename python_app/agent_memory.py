import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from memory.schema import MemoryEvent, image_fingerprint, mask_summary


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_prompt(prompt: str) -> str:
    return " ".join((prompt or "").strip().lower().split())


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return {
            "ndarray_shape": list(value.shape),
            "dtype": str(value.dtype),
            "nonzero": int(np.count_nonzero(value)),
        }
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def default_memory_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "MedicalContourAnnotationTool", "agent_memory.json")


def compute_volume_signature(volume: np.ndarray, source_path: str = "") -> str:
    """Stable, privacy-conscious signature from shape, stats, and sparse samples."""
    if volume is None:
        return "no-volume"
    arr = np.asarray(volume)
    if arr.size == 0:
        return "empty-volume"

    sample = arr
    if arr.ndim >= 3:
        z_idx = sorted({0, arr.shape[0] // 2, arr.shape[0] - 1})
        sample = arr[z_idx, :: max(1, arr.shape[1] // 64), :: max(1, arr.shape[2] // 64)]
    elif arr.ndim == 2:
        sample = arr[:: max(1, arr.shape[0] // 64), :: max(1, arr.shape[1] // 64)]

    finite = np.nan_to_num(arr.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    h = hashlib.sha1()
    h.update(str(tuple(arr.shape)).encode("utf-8"))
    h.update(str(arr.dtype).encode("utf-8"))
    h.update(os.path.basename(source_path or "").encode("utf-8"))
    stats = (
        float(np.min(finite)),
        float(np.max(finite)),
        float(np.mean(finite)),
        float(np.std(finite)),
    )
    h.update(json.dumps(stats, sort_keys=True).encode("utf-8"))
    h.update(np.ascontiguousarray(sample.astype(np.float32)).tobytes())
    return h.hexdigest()[:24]


def mask_bbox_2d(mask: Optional[np.ndarray]) -> Optional[List[int]]:
    if mask is None:
        return None
    arr = np.asarray(mask)
    if arr.ndim != 2:
        return None
    ys, xs = np.where(arr > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def mask_bbox_3d(mask_volume: Optional[np.ndarray]) -> Optional[List[int]]:
    if mask_volume is None:
        return None
    arr = np.asarray(mask_volume)
    if arr.ndim != 3:
        return None
    zs, ys, xs = np.where(arr > 0)
    if zs.size == 0 or ys.size == 0 or xs.size == 0:
        return None
    return [
        int(zs.min()),
        int(ys.min()),
        int(xs.min()),
        int(zs.max()),
        int(ys.max()),
        int(xs.max()),
    ]


@dataclass
class MemoryRecord:
    volume_signature: str
    prompt: str
    backend: str
    scope: str
    action: str
    created_at: str = field(default_factory=_utc_now)
    slice_index: Optional[int] = None
    bbox: Optional[List[int]] = None
    bbox_3d: Optional[List[int]] = None
    mask_voxels: int = 0
    mask_slices: int = 0
    elapsed_ms: float = 0.0
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return _json_safe(asdict(self))

    def to_memory_event(self, *, image=None, source_path: str = "", project_id: str = "", session_id: str = "") -> MemoryEvent:
        metadata = self.metadata or {}
        return MemoryEvent(
            image_fingerprint=image_fingerprint(image, source_path or self.volume_signature),
            image_shape=list(np.asarray(image).shape) if image is not None else [],
            modality_guess=str(metadata.get("modality_guess", metadata.get("modality", "unknown"))),
            prompt_type="text",
            text_prompt=self.prompt,
            bbox=self.bbox,
            points=metadata.get("points"),
            seed_summary=metadata.get("seed_summary"),
            selected_backend=self.backend,
            backend_version=str(metadata.get("backend_version", "")),
            model_checkpoint_id=metadata.get("model_checkpoint_id"),
            segmentation_parameters=metadata.get("segmentation_parameters", metadata.get("request", {})),
            mask_summary_statistics={
                "mask_voxels": self.mask_voxels,
                "mask_slices": self.mask_slices,
                **dict(metadata.get("mask_summary_statistics", {})),
            },
            runtime_sec=float(self.elapsed_ms) / 1000.0 if self.elapsed_ms else None,
            correction_count=metadata.get("correction_count"),
            project_id=project_id or metadata.get("project_id"),
            session_id=session_id or metadata.get("session_id"),
            provenance_id=metadata.get("provenance_id"),
        )


class ShortTermAgentMemory:
    def __init__(self, max_records: int = 200):
        self.max_records = max_records
        self.records: List[Dict[str, Any]] = []

    def record(self, record: MemoryRecord) -> None:
        self.records.append(record.to_json())
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]

    def clear(self) -> None:
        self.records.clear()

    def find_bbox(self, volume_signature: str, prompt: str, slice_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        return _find_bbox(self.records, volume_signature, prompt, slice_index, source="short")

    def summary(self) -> str:
        if not self.records:
            return "short-term: empty"
        latest = self.records[-1]
        return (
            f"short-term: {len(self.records)} record(s), latest "
            f"{latest.get('backend', '?')} {latest.get('scope', '?')} "
            f"{latest.get('elapsed_ms', 0):.1f} ms"
        )


class LongTermAgentMemory:
    def __init__(self, path: Optional[str] = None, max_records: int = 1000):
        self.path = path or default_memory_path()
        self.max_records = max_records
        self.records: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.path):
            self.records = []
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            records = payload.get("records", []) if isinstance(payload, dict) else []
            self.records = records if isinstance(records, list) else []
        except Exception:
            self.records = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        payload = {"version": 1, "records": self.records[-self.max_records :]}
        fd, tmp_path = tempfile.mkstemp(prefix="agent_memory_", suffix=".json", dir=os.path.dirname(os.path.abspath(self.path)))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def record(self, record: MemoryRecord) -> None:
        self.records.append(record.to_json())
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]
        self.save()

    def find_bbox(self, volume_signature: str, prompt: str, slice_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        return _find_bbox(self.records, volume_signature, prompt, slice_index, source="long")

    def summary(self) -> str:
        if not self.records:
            return "long-term: empty"
        return f"long-term: {len(self.records)} record(s), path={self.path}"


class AgenticMemory:
    def __init__(self, long_term_path: Optional[str] = None):
        self.short_term = ShortTermAgentMemory()
        self.long_term = LongTermAgentMemory(path=long_term_path)

    def record(
        self,
        volume_signature: str,
        prompt: str,
        backend: str,
        scope: str,
        action: str,
        *,
        slice_index: Optional[int] = None,
        mask: Optional[np.ndarray] = None,
        mask_volume: Optional[np.ndarray] = None,
        elapsed_ms: float = 0.0,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> MemoryRecord:
        bbox = mask_bbox_2d(mask)
        bbox3d = mask_bbox_3d(mask_volume)
        if bbox is None and bbox3d is not None:
            bbox = [bbox3d[2], bbox3d[1], bbox3d[5], bbox3d[4]]

        voxels = 0
        slices = 0
        if mask is not None:
            voxels = int(np.count_nonzero(mask))
            slices = 1 if voxels > 0 else 0
        if mask_volume is not None:
            arr = np.asarray(mask_volume) > 0
            voxels = int(np.count_nonzero(arr))
            slices = int(np.count_nonzero(np.any(arr, axis=(1, 2)))) if arr.ndim == 3 else 0

        record = MemoryRecord(
            volume_signature=volume_signature,
            prompt=_normalize_prompt(prompt),
            backend=backend,
            scope=scope,
            action=action,
            slice_index=slice_index,
            bbox=bbox,
            bbox_3d=bbox3d,
            mask_voxels=voxels,
            mask_slices=slices,
            elapsed_ms=float(elapsed_ms),
            message=message or "",
            metadata=metadata or {},
        )
        self.short_term.record(record)
        if persist:
            self.long_term.record(record)
        return record

    @staticmethod
    def to_canonical_event(record: MemoryRecord, *, image=None, source_path: str = "", project_id: str = "", session_id: str = "") -> MemoryEvent:
        return record.to_memory_event(image=image, source_path=source_path, project_id=project_id, session_id=session_id)

    def suggest_bbox(
        self,
        volume_signature: str,
        prompt: str,
        slice_index: Optional[int] = None,
        *,
        use_short_term: bool = True,
        use_long_term: bool = True,
    ) -> Optional[Dict[str, Any]]:
        if use_short_term:
            hit = self.short_term.find_bbox(volume_signature, prompt, slice_index)
            if hit:
                return hit
        if use_long_term:
            return self.long_term.find_bbox(volume_signature, prompt, slice_index)
        return None

    def clear_short_term(self) -> None:
        self.short_term.clear()

    def summary(self) -> str:
        return f"{self.short_term.summary()} | {self.long_term.summary()}"


def _find_bbox(
    records: List[Dict[str, Any]],
    volume_signature: str,
    prompt: str,
    slice_index: Optional[int],
    *,
    source: str,
) -> Optional[Dict[str, Any]]:
    normalized_prompt = _normalize_prompt(prompt)
    best = None
    best_score = None
    for idx, rec in enumerate(reversed(records)):
        if rec.get("volume_signature") != volume_signature:
            continue
        if rec.get("prompt") != normalized_prompt:
            continue
        bbox = _bbox_for_record(rec, slice_index)
        if bbox is None:
            continue
        rec_slice = rec.get("slice_index")
        if slice_index is not None and rec_slice is not None:
            dist = abs(int(slice_index) - int(rec_slice))
        else:
            dist = 0
        recency_penalty = idx * 0.001
        score = dist + recency_penalty
        if best_score is None or score < best_score:
            best_score = score
            best = {
                "bbox": bbox,
                "source": source,
                "backend": rec.get("backend", ""),
                "scope": rec.get("scope", ""),
                "slice_distance": dist,
                "elapsed_ms": rec.get("elapsed_ms", 0.0),
                "created_at": rec.get("created_at", ""),
            }
    return best


def _bbox_for_record(rec: Dict[str, Any], slice_index: Optional[int]) -> Optional[List[int]]:
    bbox = rec.get("bbox")
    if isinstance(bbox, list) and len(bbox) == 4:
        try:
            return [int(v) for v in bbox]
        except Exception:
            return None
    bbox3d = rec.get("bbox_3d")
    if isinstance(bbox3d, list) and len(bbox3d) == 6:
        try:
            z1, y1, x1, z2, y2, x2 = [int(v) for v in bbox3d]
        except Exception:
            return None
        if slice_index is not None and not (z1 <= int(slice_index) <= z2):
            # Still useful as a coarse prompt, just less exact.
            return [x1, y1, x2, y2]
        return [x1, y1, x2, y2]
    return None
