import json
import os

from app.configs.io import configured
from segmentation.backends import build_default_backends
from segmentation.model_registry import default_registry_path, registry_status_by_backend, validate_model_registry


EXTERNAL_ENV = {
    "cellpose": "CELLPOSE_INFER_CMD",
    "langsam": "LANGSAM_INFER_CMD",
    "medsam": "MEDSAM_INFER_CMD",
    "medsam2": "MEDSAM2_INFER_CMD",
}


def main() -> int:
    statuses = {}
    registry_path = default_registry_path()
    registry_status = registry_status_by_backend(registry_path)
    for name, entry in registry_status.items():
        env_name = EXTERNAL_ENV.get(name)
        command = str(entry.get("command", ""))
        if env_name and bool(entry.get("enabled", False)) and configured(command):
            os.environ.setdefault(env_name, command)
    for name, backend in build_default_backends().items():
        try:
            statuses[name] = backend.check_available().to_dict()
        except Exception as ex:
            statuses[name] = {
                "available": False,
                "reason": f"backend status check crashed: {ex}",
                "detected_version": None,
                "device": None,
                "extra": {},
            }
        if name in registry_status:
            statuses[name].setdefault("extra", {})
            statuses[name]["extra"]["model_registry"] = registry_status[name]
            if registry_status[name]["status"] == "NOT_CONFIGURED" and name not in {"mock", "classical"}:
                statuses[name]["extra"]["configuration_status"] = registry_status[name].get("declared_status", "NOT_CONFIGURED")
    statuses["_model_registry"] = validate_model_registry(registry_path) if registry_status else {
        "path": registry_path,
        "model_count": 0,
        "configured_count": 0,
        "errors": ["model registry file not found"],
        "models": [],
    }
    print(json.dumps(statuses, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
