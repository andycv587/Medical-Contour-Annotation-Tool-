import hashlib
import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git_commit() -> Optional[str]:
    try:
        completed = subprocess.run(["git", "rev-parse", "HEAD"], check=False, capture_output=True, text=True, timeout=5)
        if completed.returncode == 0:
            return completed.stdout.strip()
    except Exception:
        return None
    return None


def file_hash(path: Optional[str]) -> Optional[str]:
    if not path or not os.path.exists(path) or os.path.isdir(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class ProvenanceEvent:
    app_version: str
    image_shape: List[int]
    backend_name: str
    backend_version: str
    runtime_sec: float
    timestamp: str = field(default_factory=utc_now)
    git_commit_hash: Optional[str] = field(default_factory=git_commit)
    os: str = field(default_factory=platform.platform)
    python_version: str = field(default_factory=lambda: sys.version.replace("\n", " "))
    image_filename: Optional[str] = None
    image_hash: Optional[str] = None
    checkpoint_path: Optional[str] = None
    checkpoint_hash: Optional[str] = None
    prompt: Optional[str] = None
    bbox: Optional[List[int]] = None
    points: Optional[List[List[float]]] = None
    routing_decision: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_mask_path: Optional[str] = None
    export_format: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass
class AnnotationInteractionEvent:
    event_type: str = "annotation_interaction"
    timestamp: str = field(default_factory=utc_now)
    app_version: str = "0.1.0"
    git_commit_hash: Optional[str] = field(default_factory=git_commit)
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    image_id: Optional[str] = None
    image_filename: Optional[str] = None
    image_hash: Optional[str] = None
    image_shape: List[int] = field(default_factory=list)
    active_slice: Optional[int] = None
    backend_name: Optional[str] = None
    backend_version: Optional[str] = None
    selected_backend: Optional[str] = None
    prompt: Optional[str] = None
    bbox: Optional[List[int]] = None
    points: Optional[List[List[float]]] = None
    routing_decision: Dict[str, Any] = field(default_factory=dict)
    route_explanation: Optional[str] = None
    fallback_history: List[Dict[str, Any]] = field(default_factory=list)
    completion_time_sec: Optional[float] = None
    runtime_sec: Optional[float] = None
    click_count: int = 0
    prompt_count: int = 0
    correction_count: int = 0
    accepted_preview_count: int = 0
    rejected_preview_count: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)
    export_action: Optional[str] = None
    output_path: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _json_safe(asdict(self))


def build_event_from_result(
    *,
    result,
    image,
    app_version: str = "0.1.0",
    image_filename: Optional[str] = None,
    checkpoint_path: Optional[str] = None,
    prompt: Optional[str] = None,
    bbox=None,
    points=None,
    routing_decision: Optional[Dict[str, Any]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    output_mask_path: Optional[str] = None,
    export_format: Optional[str] = None,
    errors: Optional[List[str]] = None,
) -> ProvenanceEvent:
    arr = np.asarray(image)
    return ProvenanceEvent(
        app_version=app_version,
        image_shape=list(arr.shape),
        backend_name=result.backend_name,
        backend_version=result.backend_version,
        runtime_sec=float(result.runtime_sec),
        image_filename=image_filename,
        image_hash=file_hash(image_filename),
        checkpoint_path=checkpoint_path,
        checkpoint_hash=file_hash(checkpoint_path),
        prompt=prompt,
        bbox=list(bbox) if bbox is not None else None,
        points=points,
        routing_decision=routing_decision or {},
        parameters=parameters or {},
        output_mask_path=output_mask_path,
        export_format=export_format,
        warnings=list(result.warnings),
        errors=errors or [],
    )


def build_annotation_interaction_event(
    *,
    event_type: str = "annotation_interaction",
    app_version: str = "0.1.0",
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
    image_id: Optional[str] = None,
    image_filename: Optional[str] = None,
    image_hash: Optional[str] = None,
    image_shape: Optional[List[int]] = None,
    active_slice: Optional[int] = None,
    backend_name: Optional[str] = None,
    backend_version: Optional[str] = None,
    selected_backend: Optional[str] = None,
    prompt: Optional[str] = None,
    bbox: Optional[List[int]] = None,
    points: Optional[List[List[float]]] = None,
    routing_decision: Optional[Dict[str, Any]] = None,
    route_explanation: Optional[str] = None,
    fallback_history: Optional[List[Dict[str, Any]]] = None,
    completion_time_sec: Optional[float] = None,
    runtime_sec: Optional[float] = None,
    click_count: int = 0,
    prompt_count: int = 0,
    correction_count: int = 0,
    accepted_preview_count: int = 0,
    rejected_preview_count: int = 0,
    parameters: Optional[Dict[str, Any]] = None,
    export_action: Optional[str] = None,
    output_path: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AnnotationInteractionEvent:
    return AnnotationInteractionEvent(
        event_type=event_type,
        app_version=app_version,
        session_id=session_id,
        project_id=project_id,
        image_id=image_id,
        image_filename=image_filename,
        image_hash=image_hash if image_hash is not None else file_hash(image_filename),
        image_shape=list(image_shape or []),
        active_slice=active_slice,
        backend_name=backend_name,
        backend_version=backend_version,
        selected_backend=selected_backend,
        prompt=prompt,
        bbox=list(bbox) if bbox is not None else None,
        points=points,
        routing_decision=routing_decision or {},
        route_explanation=route_explanation,
        fallback_history=fallback_history or [],
        completion_time_sec=completion_time_sec,
        runtime_sec=runtime_sec,
        click_count=int(click_count),
        prompt_count=int(prompt_count),
        correction_count=int(correction_count),
        accepted_preview_count=int(accepted_preview_count),
        rejected_preview_count=int(rejected_preview_count),
        parameters=parameters or {},
        export_action=export_action,
        output_path=output_path,
        warnings=warnings or [],
        errors=errors or [],
        metadata=metadata or {},
    )


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
