import sys

import numpy as np

sys.path.insert(0, "python_app")

from ai_agents import AgenticWorkflowAgent


def test_gui_agentic_workflow_exposes_routing_explanation():
    image = np.zeros((32, 32), dtype=np.uint8)
    image[8:20, 8:20] = 255
    agent = AgenticWorkflowAgent()
    result = agent.predict(image, "cells nuclei", request={})
    text, routing = agent.explain_last_routing()
    assert result.masks
    assert "Selected backend" in text
    assert routing["selected_backend"] == "CellSeg"
    assert "ranked_candidates" in routing
    assert "unavailable_backends" in routing
    assert "fallback_history" in routing
    assert "prompt_interpretation" in routing
    assert "image_type_guess" in routing
    assert "decision_reason" in routing
