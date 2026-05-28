# Provenance

The provenance package records benchmark events, GUI interaction events, and export sidecars without storing raw image pixels or voxels.

## Headless Provenance

`benchmarks/run_benchmark.py` writes:

- `provenance/session_provenance.json`
- one sidecar JSON per exported mask
- `routing_decisions.jsonl`
- `backend_status.json`

These records include backend name/version when available, runtime, route decision, prompt/bbox/points, parameters, warnings, errors, and output paths.

## GUI Provenance

`python_app/main.py` uses `provenance/gui_logger.py` to log app/session lifecycle, image loading, slice/window changes, manual polygon actions, preview request/generation/accept/reject, backend selection, route decisions, memory suggestions, fallbacks, and exports.

If GUI logging fails, the app continues and returns a logging error record. The GUI displays the active session log path in the Files panel.

## Privacy Boundary

Logs store image filename, hash, shape, slice index, prompts, bbox/points, backend metadata, routing explanations, runtime, and output paths. Logs do not store raw image arrays by default.

## Export Sidecars

GUI exports write sidecar provenance JSON for PNG, NIfTI, TIFF stack, polygon JSON, and COCO JSON exports when logging is enabled.
