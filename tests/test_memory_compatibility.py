import sys

import numpy as np

sys.path.insert(0, "python_app")

from agent_memory import AgenticMemory
from memory import load_memory_events, save_memory_event


def test_gui_memory_record_maps_to_canonical_event_without_raw_pixels(tmp_path):
    image = np.zeros((8, 8), dtype=np.uint8)
    image[2:6, 3:7] = 1
    mem = AgenticMemory(long_term_path=str(tmp_path / "gui_memory.json"))
    record = mem.record(
        "sig",
        "cells",
        "AgenticWorkflow",
        "slice",
        "preview",
        mask=image,
        elapsed_ms=125.0,
        metadata={"backend_version": "test", "provenance_id": "prov-1"},
        persist=False,
    )
    event = mem.to_canonical_event(record, image=image, source_path="image.tif", project_id="p1", session_id="s1")
    assert event.bbox == [3, 2, 6, 5]
    assert event.provenance_id == "prov-1"
    out = tmp_path / "canonical_memory.json"
    save_memory_event(str(out), event)
    loaded = load_memory_events(str(out))
    assert "raw_image" not in loaded[0]
    assert loaded[0]["raw_image_saved"] is False


def test_gui_memory_corrupted_file_gracefully_loads_empty(tmp_path):
    path = tmp_path / "bad_memory.json"
    path.write_text("{bad", encoding="utf-8")
    mem = AgenticMemory(long_term_path=str(path))
    assert mem.long_term.records == []
