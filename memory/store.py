import json
import os
import tempfile
from typing import List

from .schema import MemoryEvent


def load_memory_events(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            events = payload.get("events", [])
        elif isinstance(payload, list):
            events = payload
        else:
            return []
        return events if isinstance(events, list) else []
    except Exception:
        return []


def save_memory_event(path: str, event: MemoryEvent, *, include_raw: bool = False) -> None:
    events = load_memory_events(path)
    events.append(event.to_dict(include_raw=include_raw))
    _write_events(path, events)


def clear_memory(path: str) -> None:
    _write_events(path, [])


def export_memory_json(path: str, output_path: str) -> None:
    events = load_memory_events(path)
    _write_events(output_path, events)


def _write_events(path: str, events: list) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = {"version": 1, "events": events}
    fd, tmp_path = tempfile.mkstemp(prefix="memory_", suffix=".json", dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
