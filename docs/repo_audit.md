# Repository Audit

Date: 2026-05-03

## Current App Entry Points

- `python_app/main.py`: Tkinter desktop GUI entry point.
- `python_app/run_python_app.bat`: Windows helper that installs `python_app/requirements.txt` and launches the GUI.
- `python_app/validate_agentic_workflow.py`: headless synthetic smoke validation for the current agentic workflow, bridge stubs, CellSeg, and memory reload.

## Current GUI Modules

- `python_app/main.py`: single-file GUI containing image loading, visualization, manual polygon annotation, metadata/layer editing, preview/apply flows, baseline segmentation, AI controls, and mask export.

## Current Segmentation Modules

- `python_app/ai_agents.py`: legacy GUI-facing backend adapters for LangSAM, MedSAM, MedSAM2, CellSeg, and AgenticWorkflow.
- `python_app/langsam_bridge_stub.py`: deterministic LangSAM-compatible command stub for smoke testing.
- `python_app/medsam_bridge_stub.py`: deterministic MedSAM-compatible command stub for smoke testing.
- `python_app/medsam2_bridge_stub.py`: deterministic MedSAM2-compatible volume command stub for smoke testing.
- Watershed and levelset implementations currently live inside `ContourAnnotationApp` in `python_app/main.py`.

## Current AgenticWorkflow / Router Modules

- `python_app/ai_agents.py` currently contains `AgenticTaskRouter` and `AgenticWorkflowAgent`.
- Routing is deterministic and can optionally call `AGENT_ROUTER_CMD`.
- Routing decisions are exposed mainly as status strings, not yet as structured benchmark logs.

## Current Memory Modules

- `python_app/agent_memory.py`: short-term and long-term geometry memory with privacy-conscious image signatures, bbox summaries, voxel/slice counts, elapsed time, and prompt/backend metadata.

## Current Export / Import Modules

- Import:
  - NIfTI volumes via `nibabel` in `python_app/main.py`.
  - 2D images and multi-page TIFF via PIL in `ContourAnnotationApp.load_image_volume`.
- Export:
  - PNG masks via `export_png_masks`.
  - NIfTI masks via `export_nifti_mask`.
- Missing:
  - COCO JSON.
  - polygon/contour JSON.
  - TIFF stack / OME-TIFF.
  - DICOM SEG / RTSTRUCT implementation.

## Current Tests

- No formal `pytest` suite exists yet.
- `python_app/validate_agentic_workflow.py` is a script-level smoke validation, not a unit test suite.

## Missing Dependencies

- Lightweight dependencies are listed in `python_app/requirements.txt`: `numpy`, `nibabel`, `pillow`, `opencv-python-headless`.
- Test/dev dependencies missing: `pytest`.
- Optional analysis dependencies missing: `scipy`, `scikit-image`, `psutil`, `matplotlib`, `pandas`, `pyyaml`.
- Heavy optional model dependencies are not installed by default: `lang-sam`, MedSAM/MedSAM2 dependencies, `cellpose`.

## Missing Model Bridges

- LangSAM/MedSAM/MedSAM2 have external command bridges in legacy adapters and stubs.
- There is no unified backend API for direct import vs external command mode.
- Cellpose/Cellpose-SAM is not yet available as a real backend.
- Checkpoint/device configuration is not yet standardized.

## Missing Benchmark Scripts

- No benchmark framework with configs, per-case outputs, metrics, provenance, routing decisions, and reports exists yet.
- No public dataset templates exist yet.
- No ablation runner exists yet.
- No baseline-comparison protocols exist yet.

## Risks For Bioinformatics Review

- The current package can be viewed as a prototype GUI or wrapper unless reproducibility, benchmarking, provenance, and documentation are strengthened.
- Real external backends are not guaranteed to be runnable from a clean environment.
- Current validation is synthetic-only and must not be reported as real-data performance.
- No public real-data benchmarks or user/time-study results are included.
- No release archive, DOI, license, citation metadata, or one-command install/test package exists yet.
- GUI workflows are not currently represented by structured provenance logs suitable for review or supplementary material.
