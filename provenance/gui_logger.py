import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import utc_now


class GuiEventLogger:
    def __init__(
        self,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        path: str = "",
        *,
        session_dir: Optional[str] = None,
        app_version: str = "0.1.0",
        enabled: bool = True,
    ):
        self.session_id = session_id or "gui-session"
        self.project_id = project_id or self.session_id
        self.app_version = app_version
        self.enabled = bool(enabled)
        self.logger = True
        self._last_error = ""
        if not path:
            path = os.environ.get("GUI_EVENT_LOG_PATH", "").strip()
        if not path and session_dir:
            path = str(Path(session_dir) / f"{self.session_id}.json")
        if not path:
            base = os.environ.get("APPDATA") or os.getcwd()
            path = os.path.join(base, "MedicalContourAnnotationTool", f"{self.session_id}.json")
        self.session_path = str(Path(path))
        Path(self.session_path).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def default(cls) -> "GuiEventLogger":
        return cls()

    def sidecar_path_for_output(self, output_path: str) -> str:
        if not output_path:
            return ""
        return f"{output_path}.provenance.json"

    def log(self, event_type: str, *, sidecar_path: str = "", **payload: Any) -> Dict[str, Any]:
        if not self.enabled or self.logger is None:
            return {"event_type": event_type, "logging_enabled": False, "logging_error": self._last_error}
        event = {
            "timestamp": utc_now(),
            "event_type": event_type,
            "app_version": self.app_version,
            "session_id": self.session_id,
            "project_id": self.project_id,
            **_json_safe(payload),
        }
        try:
            if self.session_path.endswith(".jsonl"):
                with open(self.session_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, sort_keys=True) + "\n")
            else:
                events = []
                if Path(self.session_path).exists():
                    try:
                        payload_json = json.loads(Path(self.session_path).read_text(encoding="utf-8"))
                        events = payload_json.get("events", []) if isinstance(payload_json, dict) else []
                    except Exception:
                        events = []
                events.append(event)
                Path(self.session_path).write_text(json.dumps({"version": 1, "events": events}, indent=2, sort_keys=True), encoding="utf-8")
            if sidecar_path:
                path = Path(sidecar_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(event, indent=2, sort_keys=True), encoding="utf-8")
            return event
        except Exception as ex:
            self._last_error = str(ex)
            return {"event_type": event_type, "logging_enabled": False, "logging_error": self._last_error}


GUIEventLogger = GuiEventLogger


def _json_safe(value: Any) -> Any:
    try:
        import numpy as np
    except Exception:
        np = None
    if np is not None and isinstance(value, np.ndarray):
        return {"ndarray_shape": list(value.shape), "dtype": str(value.dtype), "nonzero": int(np.count_nonzero(value))}
    if np is not None and isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value
