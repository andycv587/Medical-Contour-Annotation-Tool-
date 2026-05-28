# Workflow Architecture

`agent/router.py` and `agent/workflow.py` are the canonical package-level workflow API.

The Tkinter GUI still uses `python_app/ai_agents.py` as a GUI adapter and legacy compatibility layer. That file keeps the current GUI stable while exposing route explanations in the same shape expected from the canonical workflow:

- selected backend;
- ranked candidates;
- unavailable backends;
- fallback history;
- prompt interpretation;
- image type guess;
- decision reason.

Headless benchmark code uses the canonical `AgenticWorkflow` directly and logs routing decisions to `routing_decisions.jsonl` plus provenance sidecars.

The GUI adapter should not be described as a separate scientific workflow in the paper. It is an adapter over the same routing concept for the existing Tkinter interface.
