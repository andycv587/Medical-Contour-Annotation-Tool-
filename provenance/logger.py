import csv
import json
import os
from typing import Any, Iterable, List

from .schema import ProvenanceEvent


class ProvenanceLogger:
    def __init__(self, session_path: str):
        self.session_path = session_path
        self.events: List[dict] = []
        if os.path.exists(session_path):
            try:
                with open(session_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                self.events = payload.get("events", []) if isinstance(payload, dict) else []
            except Exception:
                self.events = []

    def log_event(self, event: Any, *, sidecar_path: str = "") -> dict:
        data = event.to_dict()
        self.events.append(data)
        self.save_session()
        if sidecar_path:
            os.makedirs(os.path.dirname(os.path.abspath(sidecar_path)), exist_ok=True)
            with open(sidecar_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
        return data

    def save_session(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.session_path)), exist_ok=True)
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "events": self.events}, f, indent=2, sort_keys=True)

    def export_csv_summary(self, path: str) -> None:
        rows = list(_flatten_events(self.events))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "backend_name", "backend_version", "runtime_sec", "image_filename", "output_mask_path", "warnings", "errors"])
            writer.writeheader()
            writer.writerows(rows)


def _flatten_events(events: Iterable[dict]):
    for event in events:
        yield {
            "timestamp": event.get("timestamp", ""),
            "backend_name": event.get("backend_name", ""),
            "backend_version": event.get("backend_version", ""),
            "runtime_sec": event.get("runtime_sec", ""),
            "image_filename": event.get("image_filename", ""),
            "output_mask_path": event.get("output_mask_path", ""),
            "warnings": "; ".join(event.get("warnings", []) or []),
            "errors": "; ".join(event.get("errors", []) or []),
        }
