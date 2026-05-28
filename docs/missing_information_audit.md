# Missing Information Audit

Audit date: 2026-05-03

Reviewer posture: strict Bioinformatics / Bioinformatics Advances software-paper review, with no fabricated datasets, checkpoints, or benchmark results.

## 1. Current Repository Structure

### Main App Entry Point

- `python_app/main.py`: Tkinter desktop GUI entry point. Contains image loading, rendering, manual polygon annotation, watershed/levelset segmentation controls, GUI-facing AI controls, memory calls, preview/apply behavior, and PNG/NIfTI export.
- `python_app/run_python_app.bat`: Windows helper that installs `python_app/requirements.txt` and launches `python_app/main.py`.
- `python_app/validate_agentic_workflow.py`: headless synthetic smoke validation for the GUI-facing agent workflow, deterministic bridge stubs, built-in CellSeg, and long-term memory reload.
- `app/backends/check.py`: CLI helper for the newer `segmentation/backends` interface. Runnable as `python -m app.backends.check`.
- `benchmarks/run_benchmark.py`: headless benchmark runner. Currently supports `synthetic_smoke` and writes `EXPERIMENT_NOT_RUN.md` for real-data templates.
- `experiments/run_ablation.py`: ablation runner. Currently supports CI-safe `mock_smoke`; real ablations are template-only.
- `Makefile`: convenience targets for install, tests, backend check, synthetic benchmark, mock ablation, and heavy install.

### GUI Modules

- `python_app/main.py`: single-file GUI implementation.
- No separate GUI package, controller/view split, or reusable GUI tests were found.

### Segmentation Modules

- GUI-facing legacy/adaptor layer:
  - `python_app/ai_agents.py`
    - `LangSAMAgent`
    - `MedSAMAgent`
    - `MedSAM2Agent`
    - `CellSegAgent`
    - `AgenticTaskRouter`
    - `AgenticWorkflowAgent`
  - `python_app/langsam_bridge_stub.py`: deterministic external bridge stub.
  - `python_app/medsam_bridge_stub.py`: deterministic external bridge stub.
  - `python_app/medsam2_bridge_stub.py`: deterministic external volume bridge stub.
- Newer backend interface layer:
  - `segmentation/backends/base.py`: backend status/result dataclasses, abstract backend API, external `.npy` bridge helper.
  - `segmentation/backends/mock_backend.py`: always-available CI/mock backend.
  - `segmentation/backends/classical_backend.py`: OpenCV classical segmentation.
  - `segmentation/backends/cellpose_backend.py`: optional Cellpose import with OpenCV fallback.
  - `segmentation/backends/langsam_backend.py`: optional LangSAM direct import or external command bridge.
  - `segmentation/backends/medsam_backend.py`: external MedSAM bridge; direct import explicitly not implemented.
  - `segmentation/backends/medsam2_backend.py`: external MedSAM2 bridge; direct import explicitly not implemented.
  - `segmentation/backends/__init__.py`: backend registry.
- Classical watershed/levelset implementations also exist inside `python_app/main.py`.

### Agent/Router Modules

- GUI-facing router:
  - `python_app/ai_agents.py`: deterministic heuristic router plus optional `AGENT_ROUTER_CMD` external planner hook.
- Newer workflow/router layer:
  - `agent/router.py`: `AgenticRouter`, `RoutingDecision`, prompt/image-type heuristics.
  - `agent/workflow.py`: `AgenticWorkflow`, fallback execution, routing explanation.
  - `agent/routing_rules.yaml`: human-readable routing rule sketch.
  - `agent/__init__.py`: exports workflow/router classes.
- Publication risk: there are two workflow/router implementations. The paper and package need one authoritative API, or a clear compatibility explanation.

### Memory Modules

- `python_app/agent_memory.py`: short-term and long-term geometry/performance memory.
  - Stores prompt, backend, scope, action, 2D/3D bounding boxes, voxel/slice counts, elapsed time, message, and metadata.
  - Uses a privacy-conscious volume signature rather than storing image voxels.
  - Default long-term path is `%APPDATA%/MedicalContourAnnotationTool/agent_memory.json` on Windows, or the user home directory fallback.
- `memory/schema.py`: separate package-level memory event schema, image fingerprinting, and mask summaries.
- `memory/store.py`: JSON memory event store.
- `memory/reuse.py`: prompt/bbox suggestion helpers.
- `memory/__init__.py`: exports package-level memory helpers.
- Publication risk: there are now two memory implementations, `python_app/agent_memory.py` and the package-level `memory/` module. They need a single documented role or a migration path.

### Export/Import Modules

- Import:
  - `python_app/main.py` loads 3D NIfTI files through `nibabel`.
  - `python_app/main.py` loads PNG/JPEG/BMP and single/multi-page TIFF images through PIL.
  - NIfTI loading squeezes data and moves the smallest dimension to slice axis 0.
- Export:
  - `python_app/main.py` exports committed mask slices to PNG.
  - `python_app/main.py` exports committed masks to NIfTI when the source was NIfTI.
- Reusable import/export helpers:
  - `contour_io/importers.py`: NIfTI and common image/TIFF loading helper.
  - `contour_io/exporters.py`: PNG, NIfTI, TIFF stack, polygon JSON, and COCO JSON export helpers.
  - `contour_io/__init__.py`: exports import/export helpers.
  - `io/exporters.py` and `io/importers.py`: compatibility files that re-export `contour_io`; normal imports should prefer `contour_io` because Python's standard-library `io` shadows this directory.
- Missing/limited import/export formats:
  - OME-TIFF is not implemented.
  - DICOM SEG and RTSTRUCT are explicitly documented as not implemented in `docs/dicom_rtstruct_limitations.md`.
  - GUI integration still exposes only PNG and NIfTI export; the reusable helper formats are not yet wired into the Tkinter GUI.

### Tests

- `tests/` contains a lightweight `pytest` suite:
  - `tests/test_agent_router.py`
  - `tests/test_backends.py`
  - `tests/test_benchmark_execution.py`
  - `tests/test_exporters.py`
  - `tests/test_importers_and_cli.py`
  - `tests/test_memory.py`
  - `tests/test_provenance.py`
  - `tests/conftest.py`
- `python_app/validate_agentic_workflow.py` remains an additional GUI-facing workflow smoke validation script.
- `python -m pytest -q` was run during this audit and passed 17 tests.
- `pytest -q` initially failed in this local shell before editable installation/path normalization, so reviewer docs should prefer `python -m pytest -q` or require `python -m pip install -e .` first.
- No automated GUI test suite was found.

### Benchmark Scripts

- `benchmarks/run_benchmark.py`: synthetic smoke benchmark runner and real-data template guard.
- `benchmarks/datasets.py`: generated synthetic organ and cell cases.
- `benchmarks/metrics.py`: binary Dice/IoU/precision/recall/Hausdorff95 and simple object precision/recall/F1. AJI/split/merge metrics are placeholders.
- `benchmarks/report.py`: writes CSV and Markdown benchmark reports.
- `benchmarks/configs/synthetic_smoke.yaml`: runnable synthetic smoke config.
- `benchmarks/configs/medical_3d_template.yaml`: template for user-provided MSD/BTCV/LiTS/KiTS/FLARE-style data.
- `benchmarks/configs/microscopy_template.yaml`: template for user-provided Cellpose/BBBC/MoNuSeg/CPM-style data.
- `experiments/run_ablation.py`: mock smoke ablation runner; real ablations write `EXPERIMENT_NOT_RUN.md`.
- `experiments/ablation_configs/*.yaml`: backend, memory, router, and mock smoke ablation templates.
- No real-data benchmark has been run. Dataset paths and ground-truth masks remain missing.

### Documentation

- `README.md`: describes current app features, bridge protocols, memory behavior, and synthetic validation command.
- `docs/repo_audit.md`: earlier repository audit summary.
- `INSTALL.md`: lightweight, GUI, and heavy-backend installation notes.
- `ENVIRONMENT.md`: supported environment and environment variables.
- `docs/reviewer_quickstart.md`: reviewer commands and expected lightweight behavior.
- `docs/availability_statement.md`: placeholder availability statement.
- `docs/reproducibility_checklist.md`: publication reproducibility checklist.
- `docs/baselines.md`: baseline protocol templates.
- `docs/usability_study_protocol.md`: usability/time-study protocol template.
- `docs/dicom_rtstruct_limitations.md`: clinical format limitation note.
- `docs/project_decisions.md`: Andy's current publication, data, backend, GUI, export, and reproducibility decisions.
- `docs/datasets.md`: public dataset priority and manifest policy.
- `paper_assets/software_note_outline.md` and `paper_assets/tables/*.md`: paper outline and placeholder tables.
- No API reference.
- No concrete public dataset download instructions with selected dataset versions/paths.
- No completed real benchmark report.

### Config Files

- `.gitignore`: ignores Python cache/build artifacts, bridge temp files, editor files, and local NIfTI volumes.
- `pyproject.toml`: setuptools package metadata with lightweight dependencies and optional `dev`, `analysis`, and `heavy` extras. Author field remains `TO_BE_FILLED`.
- `requirements.txt`: root lightweight/dev requirements including `pytest`.
- `python_app/requirements.txt`: `numpy`, `nibabel`, `pillow`, `opencv-python-headless`.
- `environment.yml`: conda environment template.
- `Dockerfile`: lightweight container that installs `.[dev]` and runs the synthetic benchmark by default. Not built during this audit.
- `.github/workflows/tests.yml`: CI workflow for editable install, `pytest -q`, and synthetic benchmark.
- `LICENSE`: MIT license text, but copyright holder is `TO_BE_FILLED`.
- `CITATION.cff`: citation metadata placeholder with `TO_BE_FILLED` author and repository URL.
- `CHANGELOG.md`: initial 0.1.0 scaffold changelog.
- `agent/routing_rules.yaml`: human-readable routing rules.
- Missing:
  - resolved author/copyright/repository metadata
  - release tag and DOI/archive metadata
  - configured real model/checkpoint entries beyond `configs/model_registry.example.yaml`

### Model/Checkpoint Handling

- GUI-facing bridge configuration uses environment variables and GUI fields:
  - `LANGSAM_INFER_CMD`
  - `MEDSAM_INFER_CMD`
  - `MEDSAM2_INFER_CMD`
  - `AGENT_ROUTER_CMD`
- `python_app/main.py` pre-fills LangSAM, MedSAM, and MedSAM2 command fields with deterministic local stubs.
- The newer backend layer can report availability through `python -m app.backends.check`.
- `segmentation/backends/medsam_backend.py` and `segmentation/backends/medsam2_backend.py` preserve `checkpoint_path` metadata in result summaries.
- `provenance/schema.py` can record checkpoint path/hash when supplied.
- `configs/model_registry.example.yaml` defines required checkpoint fields and is intentionally `NOT_CONFIGURED`.
- No checkpoint resolver/downloader exists, and no real model registry entry is configured.
- Real backend status in the inspected environment:
  - LangSAM: unavailable, `lang_sam` import missing unless external command is configured.
  - MedSAM: unavailable, `medsam` import missing unless external command is configured.
  - MedSAM2: unavailable, `medsam2` import missing unless external command is configured.
  - Cellpose: unavailable as a real Cellpose import; OpenCV fallback is available.
  - Classical and mock backends are available.

## 2. Current Feature Status

| Feature | Status | Evidence / limitation |
|---|---|---|
| Tkinter desktop GUI | Implemented but untested | `python_app/main.py` is substantial; no GUI tests or scripted screenshot validation are present as maintained tests. |
| 3D NIfTI loading | Implemented but untested | Implemented in `choose_nifti`; no formal tests or sample NIfTI data. |
| 2D image and multi-page TIFF loading | Implemented and partially tested | Implemented in GUI and helper layer; helper tests cover PNG and TIFF stack loading. |
| Manual polygon annotation | Implemented but untested | Polygon drawing, finish/cancel, undo/redo, selection, label/color/layer metadata exist in GUI; no automated GUI tests. |
| Overlay preview/apply workflow | Implemented but untested | Preview and committed overlay structures exist; no tests. |
| Watershed segmentation | Implemented but untested | Implemented inside GUI and newer classical backend; no formal validation. |
| Levelset-like segmentation | Implemented but untested | Implemented as lightweight active-contour-like iteration; no formal validation against reference method. |
| Built-in CellSeg/OpenCV cell segmentation | Implemented and synthetic-tested | `CellSegAgent` is exercised by `validate_agentic_workflow.py`; synthetic cell Dice is reported by the script only. |
| Real Cellpose backend | Partially implemented | `segmentation/backends/cellpose_backend.py` attempts Cellpose import and falls back to OpenCV. Real Cellpose is not installed in this environment and is not wired into the GUI-facing agent registry. |
| LangSAM external bridge | Implemented and synthetic-tested with stub | Stub command works in validation. Real LangSAM command/checkpoint not provided. |
| LangSAM direct import | Partially implemented | Direct import code exists, but `lang_sam` is unavailable here and no tests/checkpoints are present. |
| MedSAM external bridge | Partially implemented | Bridge protocol and stub exist. Real command/checkpoint not provided. Direct adapter is explicitly not wired. |
| MedSAM direct import | Stub/mock only | Code reports direct package detection but says runtime adapter is not wired. |
| MedSAM2 external bridge | Implemented and synthetic-tested with stub | Stub volume bridge works in validation. Real command/checkpoint not provided. |
| MedSAM2 direct import | Stub/mock only | Code reports direct package detection but says runtime adapter is not wired. |
| AgenticWorkflow router, GUI-facing | Implemented and synthetic-tested | `validate_agentic_workflow.py` tests routing to MedSAM2 stub and CellSeg. |
| External LLM/VLM router hook | Partially implemented | `AGENT_ROUTER_CMD` protocol exists; no reference router, tests, or provenance logs. |
| AgenticWorkflow router, newer package layer | Implemented and tested | `tests/test_agent_router.py` covers routing choices, fallback history, and explanation output. |
| Router explanation | Partially implemented | Newer `AgenticWorkflow.explain_routing()` is tested and benchmark routing decisions are logged; GUI still exposes mainly message strings. |
| Short-term geometry memory | Implemented and synthetic-tested | `AgenticMemory` smoke-tested for bbox reuse in validation. |
| Long-term geometry memory | Implemented and synthetic-tested | Validation writes/reloads temporary memory file. No privacy/security review or schema version tests. |
| Full provenance logging | Partially implemented | `provenance/` logs benchmark session/sidecar provenance with backend, runtime, route, parameters, hashes when paths exist. GUI actions/exports are not yet fully wired to provenance. |
| Usability/event logging schema | Partially implemented | `AnnotationInteractionEvent` can store completion time, clicks, prompts, corrections, preview decisions, backend, fallback, export action, and route explanation. GUI wiring is still pending. |
| PNG mask export | Implemented and unit-tested in helper layer | GUI implementation exists; `contour_io.export_png_mask` is tested. |
| NIfTI mask export | Implemented and partially tested | GUI implementation exists; helper export is tested for shape. Orientation/header round-trip validation is still missing. |
| TIFF stack export | Implemented and unit-tested in helper layer | `contour_io.export_tiff_stack` is tested; GUI integration missing. |
| COCO/polygon JSON export | Implemented and unit-tested in helper layer | Helper functions are tested; GUI integration missing. |
| OME-TIFF export | Missing | No implementation found. |
| DICOM SEG/RTSTRUCT export | Missing by design | Not implemented; limitation documented in `docs/dicom_rtstruct_limitations.md`. |
| Backend availability checker | Implemented and tested for lightweight status | `python -m app.backends.check` works and is covered by tests; real heavy backend checks remain dependent on user configuration. |
| One-command smoke test | Implemented for lightweight mode | `python -m pytest -q`, `python python_app/validate_agentic_workflow.py`, and synthetic benchmark run locally. |
| Public dataset support | Partially implemented | Dataset templates exist, but no selected datasets, paths, labels, or download instructions. |
| Synthetic benchmark | Implemented for smoke testing | `benchmarks/run_benchmark.py` writes metrics, masks, routing decisions, figures, report, and provenance for synthetic cases. |
| Real-data benchmark | Partially implemented | Runner has template guard only; no real datasets configured or run. |
| Baseline comparison | Partially implemented | Protocol document exists; no baseline results. |
| Ablation framework | Partially implemented | Mock smoke ablation runs; real ablations are templates only. |
| Usability/time study | Partially implemented | Protocol and form templates exist; no participants, task data, GUI event logger, or results. |
| Installable package | Partially implemented | `pyproject.toml` exists, but author/repository metadata are placeholders and editable install was not re-tested during this audit. |
| CI | Partially implemented | `.github/workflows/tests.yml` exists; remote CI run status unknown. |
| License | Partially implemented | MIT `LICENSE` exists, but copyright holder is `TO_BE_FILLED`; Andy must confirm. |
| Citation metadata | Partially implemented | `CITATION.cff` exists with placeholder author/repository metadata; no DOI/archive. |

## 3. Current Publication-Readiness Status

| Criterion | Status | Notes |
|---|---|---|
| Installability | PARTIAL | `pyproject.toml`, root requirements, `environment.yml`, Dockerfile, `INSTALL.md`, and Windows batch file exist. Metadata/placeholders and clean-environment install verification remain. |
| One-command smoke test | PARTIAL | `python -m pytest -q`, `python python_app/validate_agentic_workflow.py`, synthetic benchmark, and mock ablation pass locally. Need clean-env/CI confirmation. |
| Model backend availability check | PARTIAL | `python -m app.backends.check` works for newer backend layer. GUI has a backend check button. Need documented expected output and real backend config checks. |
| Public dataset support | PARTIAL | Dataset priorities are decided and templates exist. Actual MSD/Cellpose/BBBC download instructions, paths, and masks are missing. |
| Synthetic benchmark | PARTIAL | Benchmark framework exists and runs, but synthetic results remain smoke-only. |
| Real-data benchmark | MISSING | No real-data benchmark has been configured or run. |
| Ablation framework | PARTIAL | Mock smoke ablation runs; real ablations are template-only. |
| Baseline comparison | PARTIAL | Baseline protocol document exists; no results. |
| Provenance logging | PARTIAL | Headless benchmark provenance works; GUI/session/export provenance is incomplete. |
| Memory validation | PARTIAL | Package memory unit tests and GUI-facing synthetic reload smoke exist. Need task-level validation. |
| Documentation | PARTIAL | README, install, environment, reviewer quickstart, project decisions, dataset plan, baselines, availability placeholder, and paper templates exist. Dataset/model specifics remain missing. |
| License | PARTIAL | MIT file exists with placeholder copyright. |
| Citation metadata | PARTIAL | `CITATION.cff` exists with placeholder metadata; DOI/archive missing. |
| Release/archive readiness | PARTIAL | Version and release scaffolding exist; release tag, archive, DOI, and filled metadata are missing. |
| Reviewer quickstart | PARTIAL | `docs/reviewer_quickstart.md` exists; needs clean-env verification and finalized expected outputs. |

## 4. Immediate Rejection Risks

As a strict Bioinformatics reviewer, I would flag the following risks immediately:

- Novelty risk: The current repository could be perceived as a lightweight GUI plus wrappers around known segmentation tools unless the agentic routing, memory/provenance, and reproducible workflow contributions are made concrete, tested, and compared.
- Wrapper/glue-code concern: LangSAM, MedSAM, MedSAM2, and Cellpose are not demonstrated as real integrated backends in this environment. Several paths are bridge protocols or deterministic stubs. The paper must not imply real model performance unless real checkpoints and scripts are supplied.
- Lack of real benchmark: Synthetic validation is useful for engineering but insufficient for a Bioinformatics software paper. Public real-data experiments with ground truth are needed.
- Lack of baseline comparison: No comparisons exist against standard tools or native workflows such as 3D Slicer, ITK-SNAP, QuPath, Cellpose, micro-SAM, MedSAM/MedSAM2, or LangSAM.
- Weak Bioinformatics scope: A broad "medical contour annotation" tool may be considered outside Bioinformatics unless the scope emphasizes bioimage informatics, microscopy/cell analysis, reproducible annotation workflows, or biological image datasets.
- Unavailable software risk: package/CI/license/citation scaffolding now exists, but placeholder metadata, lack of release archive/DOI, and unverified clean install remain risks.
- Incomplete installation: lightweight install docs exist, but dependency versions are mostly unpinned and heavy backend setup remains external.
- Missing test data: synthetic generated data exists; no committed licensed sample images/masks or selected public-data download instructions are present.
- Unsupported claims risk: README language around LangSAM/MedSAM/MedSAM2 must remain clearly qualified as bridge/stub-capable unless real backends are configured and validated.
- Missing reproducibility artifacts: synthetic run configs, provenance logs, and result templates exist; real-data manifests, model configs, command logs for heavy backends, and completed real results are missing.
- Model checkpoint ambiguity: a registry template now exists, but no real checkpoint paths, hashes, download instructions, or license constraints are filled in.
- Two workflow-layer risk: `python_app/ai_agents.py` and `agent/workflow.py` define overlapping agentic workflow concepts. Reviewers and users need a single authoritative path.
- GUI-only risk: Much functionality is embedded in one large GUI file, which makes automated testing and reproducible headless execution harder.
- Export interoperability risk: PNG/NIfTI export exists, but no round-trip or orientation validation is present. Clinical formats should not be claimed.
- Memory/privacy risk: The memory module avoids raw image storage, but privacy guarantees, schema, retention, and opt-out behavior need explicit documentation and tests.
- Results reporting risk: Synthetic Dice values from the smoke script must not be presented as benchmark performance or real-data evidence.
