import json

import numpy as np

from provenance.logger import ProvenanceLogger
from provenance.schema import build_annotation_interaction_event, build_event_from_result
from segmentation.backends.mock_backend import MockBackend


def test_provenance_sidecar_and_session(tmp_path):
    image = np.zeros((16, 16), dtype=np.uint8)
    result = MockBackend().segment(image, prompt="object")
    event = build_event_from_result(result=result, image=image, prompt="object", output_mask_path="mask.png", export_format="png")
    logger = ProvenanceLogger(str(tmp_path / "session.json"))
    logger.log_event(event, sidecar_path=str(tmp_path / "sidecar.json"))
    assert (tmp_path / "sidecar.json").exists()
    payload = json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))
    assert len(payload["events"]) == 1
    logger.export_csv_summary(str(tmp_path / "summary.csv"))
    assert (tmp_path / "summary.csv").exists()


def test_annotation_interaction_event_logs_user_study_metrics(tmp_path):
    event = build_annotation_interaction_event(
        session_id="s1",
        project_id="p1",
        image_id="img1",
        selected_backend="AgenticWorkflow",
        route_explanation="selected Cellpose for nuclei prompt",
        fallback_history=[{"backend": "langsam", "status": "unavailable"}],
        completion_time_sec=12.5,
        click_count=3,
        prompt_count=1,
        correction_count=2,
        accepted_preview_count=1,
        rejected_preview_count=0,
        export_action="polygon_json",
        output_path="mask.json",
    )
    logger = ProvenanceLogger(str(tmp_path / "session.json"))
    logged = logger.log_event(event)
    assert logged["event_type"] == "annotation_interaction"
    assert logged["click_count"] == 3
    assert logged["route_explanation"]
