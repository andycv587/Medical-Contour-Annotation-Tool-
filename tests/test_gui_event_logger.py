import json

import numpy as np

from provenance.gui_logger import GuiEventLogger


def test_gui_event_logger_writes_session_and_sidecar_without_pixels(tmp_path):
    logger = GuiEventLogger(session_dir=str(tmp_path), session_id="session-1", project_id="project-1")
    out = tmp_path / "mask.png"
    out.write_bytes(b"fake")
    sidecar = logger.sidecar_path_for_output(str(out))

    event = logger.log(
        "export_mask",
        sidecar_path=sidecar,
        image_filename="image.tif",
        image_shape=[1, 8, 8],
        active_slice=0,
        selected_backend="mock",
        prompt="cells",
        bbox=[1, 1, 4, 4],
        routing_decision={"selected_backend": "mock"},
        parameters={"mask_summary": np.zeros((8, 8), dtype=np.uint8)},
        output_path=str(out),
        export_action="png",
    )

    assert event["event_type"] == "export_mask"
    payload = json.loads((tmp_path / "session-1.json").read_text(encoding="utf-8"))
    assert payload["events"][0]["parameters"]["mask_summary"]["ndarray_shape"] == [8, 8]
    assert "raw_image" not in json.dumps(payload)
    assert json.loads(open(sidecar, encoding="utf-8").read())["output_path"] == str(out)


def test_gui_event_logger_fails_closed(tmp_path):
    logger = GuiEventLogger(session_dir=str(tmp_path), session_id="session-2")
    logger.logger = None
    logger.enabled = False
    event = logger.log("app_start")
    assert event["logging_enabled"] is False
