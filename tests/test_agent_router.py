import numpy as np

from agent.router import AgenticRouter
from agent.workflow import AgenticWorkflow
from segmentation.backends.base import BackendStatus
from segmentation.backends.mock_backend import MockBackend


class FailingBackend(MockBackend):
    name = "failing"

    def segment(self, *args, **kwargs):
        raise RuntimeError("intentional failure")


def test_router_prefers_cellpose_for_cell_prompt():
    router = AgenticRouter()
    image = np.zeros((64, 64), dtype=np.uint8)
    statuses = {"cellpose": BackendStatus(True, "ok").to_dict(), "classical": BackendStatus(True, "ok").to_dict()}
    decision = router.route(image, prompt="segment nuclei in DAPI microscopy", backend_statuses=statuses)
    assert decision.selected_backend == "cellpose"
    assert "cellpose" in decision.ranked_candidates


def test_router_prefers_medsam2_for_3d_bbox_seed():
    router = AgenticRouter()
    image = np.zeros((4, 32, 32), dtype=np.uint8)
    statuses = {"medsam2": BackendStatus(True, "ok").to_dict(), "classical": BackendStatus(True, "ok").to_dict()}
    decision = router.route(image, prompt="liver", bbox=[4, 4, 20, 20], seed=np.ones_like(image), metadata={"modality": "ct"}, backend_statuses=statuses)
    assert decision.selected_backend == "medsam2"


def test_workflow_fallback_history_records_failure():
    image = np.zeros((32, 32), dtype=np.uint8)
    image[8:20, 8:20] = 255
    wf = AgenticWorkflow(backends={"failing": FailingBackend(), "mock": MockBackend()})
    wf.router.preferred_order = ["failing", "mock"]
    # Force a ranking where failing comes before mock.
    wf.router.rank_candidates = lambda *args, **kwargs: (["failing", "mock"], "test ranking")
    run = wf.segment(image, prompt="object")
    assert run.routing.selected_backend == "mock"
    assert any(item["backend"] == "failing" and item["status"] == "failed" for item in run.routing.fallback_history)


def test_explain_routing_returns_text_and_json():
    wf = AgenticWorkflow(backends={"mock": MockBackend()})
    text, data = wf.explain_routing(np.zeros((16, 16), dtype=np.uint8), prompt="object")
    assert "Selected backend" in text
    assert "ranked_candidates" in data
