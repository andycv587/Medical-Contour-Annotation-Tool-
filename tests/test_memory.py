import json

import numpy as np

from memory import clear_memory, load_memory_events, retrieve_similar_prompt, save_memory_event, suggest_prompt_from_memory
from memory.schema import MemoryEvent, image_fingerprint, mask_summary


def test_memory_persists_without_raw_pixels(tmp_path):
    image = np.zeros((8, 8), dtype=np.uint8)
    event = MemoryEvent(
        image_fingerprint=image_fingerprint(image),
        image_shape=[8, 8],
        modality_guess="microscopy",
        prompt_type="text",
        text_prompt="cells",
        bbox=[1, 1, 5, 5],
        selected_backend="cellpose",
        backend_version="test",
        mask_summary_statistics=mask_summary(image),
        raw_image=image,
    )
    path = tmp_path / "memory.json"
    save_memory_event(str(path), event)
    loaded = load_memory_events(str(path))
    assert len(loaded) == 1
    assert "raw_image" not in loaded[0]
    assert loaded[0]["raw_image_saved"] is False


def test_similar_prompt_retrieval(tmp_path):
    path = tmp_path / "memory.json"
    event = MemoryEvent(
        image_fingerprint="abc",
        image_shape=[8, 8],
        modality_guess="microscopy",
        prompt_type="text",
        text_prompt="nuclei",
        bbox=[1, 1, 4, 4],
        selected_backend="cellpose",
        backend_version="test",
    )
    save_memory_event(str(path), event)
    events = load_memory_events(str(path))
    hit = retrieve_similar_prompt(events, image_fingerprint="abc", text_prompt="nucleus", modality_guess="microscopy")
    assert hit["bbox"] == [1, 1, 4, 4]
    suggestion = suggest_prompt_from_memory(events, {"image_fingerprint": "abc", "text_prompt": "nucleus"})
    assert suggestion["selected_backend"] == "cellpose"


def test_corrupted_memory_fails_gracefully(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert load_memory_events(str(path)) == []


def test_clear_memory(tmp_path):
    path = tmp_path / "memory.json"
    path.write_text(json.dumps({"events": [{"x": 1}]}), encoding="utf-8")
    clear_memory(str(path))
    assert load_memory_events(str(path)) == []
