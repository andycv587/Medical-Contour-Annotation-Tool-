import hashlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from app.configs.io import load_structured_config


REQUIRED_FIELDS = ("id", "backend", "backend_mode", "checkpoint_path", "checkpoint_sha256", "source_url", "license")
PLACEHOLDER_VALUES = {"", "TO_BE_CONFIGURED", "NOT_CONFIGURED", "optional_builtin_or_TO_BE_CONFIGURED"}
LIGHTWEIGHT_BACKENDS = {"mock", "classical"}
CHECKPOINT_OPTIONAL_BACKENDS = {"cellpose"}


@dataclass
class ModelRegistryEntry:
    id: str = ""
    backend: str = ""
    backend_mode: str = "external_command"
    enabled: bool = False
    command: str = "NOT_CONFIGURED"
    repo_path: str = "NOT_CONFIGURED"
    checkpoint_path: str = "NOT_CONFIGURED"
    checkpoint_version: str = "NOT_CONFIGURED"
    checkpoint_sha256: str = "NOT_CONFIGURED"
    source_url: str = "NOT_CONFIGURED"
    license: str = "NOT_CONFIGURED"
    python_executable: str = ""
    extra_args: List[str] = None
    device: str = ""
    command_env: str = ""
    status: str = "NOT_CONFIGURED"

    def __post_init__(self) -> None:
        if self.extra_args is None:
            self.extra_args = []

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    def is_configured(self) -> bool:
        if self.backend in LIGHTWEIGHT_BACKENDS:
            return True
        values = [getattr(self, field) for field in self._required_fields()]
        return bool(self.enabled) and self.status != "NOT_CONFIGURED" and all(str(value).strip() not in PLACEHOLDER_VALUES for value in values)

    def validate(self, *, verify_files: bool = False) -> List[str]:
        errors: List[str] = []
        if self.backend in LIGHTWEIGHT_BACKENDS:
            return errors
        for field in self._required_fields():
            value = str(getattr(self, field, "") or "").strip()
            if not value:
                errors.append(f"{self.id}: missing required field {field}")
        if not self.is_configured():
            return errors
        if verify_files:
            if not os.path.exists(self.checkpoint_path):
                errors.append(f"{self.id}: checkpoint_path does not exist: {self.checkpoint_path}")
            else:
                actual = sha256_file(self.checkpoint_path)
                if actual.lower() != self.checkpoint_sha256.lower():
                    errors.append(f"{self.id}: sha256 mismatch")
        return errors

    def _required_fields(self) -> tuple[str, ...]:
        if self.backend in CHECKPOINT_OPTIONAL_BACKENDS:
            return tuple(field for field in REQUIRED_FIELDS if field not in {"checkpoint_path", "checkpoint_sha256"})
        return REQUIRED_FIELDS


def load_model_registry(path: str) -> List[ModelRegistryEntry]:
    payload = load_structured_config(path)
    models_raw = payload.get("models", []) if isinstance(payload, dict) else []
    models = _normalize_models(models_raw)
    entries = []
    for item in models:
        if isinstance(item, dict):
            item = dict(item)
            if "backend_mode" not in item and "integration" in item:
                item["backend_mode"] = item.get("integration")
            if "checkpoint_sha256" not in item and "sha256" in item:
                item["checkpoint_sha256"] = item.get("sha256")
            fields = {}
            for key, field_def in ModelRegistryEntry.__dataclass_fields__.items():
                if key in item:
                    fields[key] = item[key]
                elif field_def.default is not field_def.default_factory:
                    fields[key] = field_def.default
            entries.append(ModelRegistryEntry(**fields))
    return entries


def validate_model_registry(path: str, *, verify_files: bool = False) -> Dict[str, object]:
    entries = load_model_registry(path)
    errors: List[str] = []
    for entry in entries:
        errors.extend(entry.validate(verify_files=verify_files))
    return {
        "path": path,
        "model_count": len(entries),
        "configured_count": sum(1 for entry in entries if entry.is_configured()),
        "errors": errors,
        "models": [entry.to_dict() for entry in entries],
    }


def default_registry_path() -> str:
    configured = os.environ.get("MODEL_REGISTRY_PATH", "").strip()
    if configured:
        return configured
    local_registry = os.path.join("configs", "model_registry.local.yaml")
    if os.path.exists(local_registry):
        return local_registry
    local = os.path.join("configs", "models.local.yaml")
    if os.path.exists(local):
        return local
    return os.path.join("configs", "models.example.yaml")


def load_default_model_registry() -> List[ModelRegistryEntry]:
    path = default_registry_path()
    if not os.path.exists(path):
        return []
    return load_model_registry(path)


def registry_status_by_backend(path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    path = path or default_registry_path()
    if not os.path.exists(path):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for entry in load_model_registry(path):
        out[entry.backend] = {
            "id": entry.id,
            "enabled": bool(entry.enabled),
            "status": "CONFIGURED" if entry.is_configured() else "NOT_CONFIGURED",
            "declared_status": entry.status,
            "backend_mode": entry.backend_mode,
            "command": entry.command,
            "repo_path": entry.repo_path,
            "checkpoint_path": entry.checkpoint_path,
            "checkpoint_sha256": entry.checkpoint_sha256,
            "source_url": entry.source_url,
            "license": entry.license,
            "device": entry.device,
        }
    return out


def _normalize_models(models_raw: Any) -> List[Dict[str, Any]]:
    if isinstance(models_raw, list):
        return [item for item in models_raw if isinstance(item, dict)]
    if isinstance(models_raw, dict):
        out = []
        for backend, item in models_raw.items():
            if isinstance(item, dict):
                data = dict(item)
                data.setdefault("backend", str(backend))
                data.setdefault("id", str(backend))
                out.append(data)
        return out
    return []


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
