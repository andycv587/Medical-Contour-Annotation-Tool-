# Next Implementation Plan

This plan continues only with work that is conservative and does not require fabricated datasets, checkpoints, or results.

## Priority 1

Goal: make the lightweight package reproducible, auditable, and testable without heavy model dependencies. Several scaffolds now exist; Priority 1 is to consolidate them, wire them into the GUI where needed, and verify clean-environment behavior.

| Task | Exact files to create or edit | Exact commands to run | Expected outputs | Risk level | User input needed |
|---|---|---|---|---|---|
| Backend interface | Edit `segmentation/backends/base.py`, `segmentation/backends/__init__.py`, `agent/workflow.py`; document whether `python_app/ai_agents.py` is legacy GUI adapter or migrate GUI to package workflow | `python -m compileall segmentation agent python_app`; `python -m pytest -q` | One documented workflow path and compatibility note | Medium | No |
| Backend availability checker | Edit `app/backends/check.py`, `README.md`, `INSTALL.md`, `docs/reviewer_quickstart.md` | `python -m app.backends.check`; `python -m pytest tests/test_backends.py` | JSON backend status with mock/classical/fallback/stub distinctions and expected output | Low | No |
| Model registry | Maintain `configs/model_registry.example.yaml` and `segmentation/model_registry.py`; add real local registry only after checkpoints are known | `python -m pytest tests/test_model_registry.py` | Validated `NOT_CONFIGURED` registry template; no fake checkpoint claims | Low | Yes for real entries |
| Router explanation | Edit `agent/router.py`, `agent/workflow.py`, `python_app/main.py`; optionally add GUI explanation panel | `python -m pytest tests/test_agent_router.py`; `python -m compileall python_app` | Structured route explanation visible/loggable in GUI, CLI, and benchmark outputs | Medium | No |
| Memory schema | Reconcile `python_app/agent_memory.py` with package-level `memory/`; create `docs/memory_schema.md` | `python -m pytest tests/test_memory.py`; `python python_app/validate_agentic_workflow.py` | Single documented memory schema with GUI compatibility | Medium | No |
| Provenance logger | Edit `python_app/main.py` to use `provenance/` for GUI actions/exports; keep benchmark provenance | `python -m pytest tests/test_provenance.py`; `python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke` | Session/sidecar logs for GUI and headless workflows | Medium | No |
| Synthetic benchmark | Maintain `benchmarks/run_benchmark.py`, metrics/report/provenance outputs; add clean-env docs and prevent synthetic values from entering real tables | `python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke`; `python -m app.provenance.inspect results/synthetic_smoke/provenance/session_provenance.json` | JSON/CSV synthetic smoke report; no real-data claims | Low | No |
| Tests | Keep expanding lightweight tests, especially GUI-free import/export/orientation and real-template dry runs | `python -m pytest -q` | Lightweight suite that passes without heavy models | Medium | No |
| README/INSTALL | Edit `README.md`, `INSTALL.md`, `ENVIRONMENT.md`, `docs/reviewer_quickstart.md` | Run documented commands from a clean shell | Reviewer can run install, backend check, tests, synthetic benchmark, and provenance inspect | Low | No |
| Dataset templates | Maintain `docs/datasets.md`, `benchmarks/configs/medical_3d_template.yaml`, `benchmarks/configs/microscopy_template.yaml` | `python benchmarks/run_benchmark.py --config benchmarks/configs/medical_3d_template.yaml --output results/real_dry_run` | MSD-first and Cellpose/BBBC-first templates that refuse to fabricate results | Low | Yes for paths |

Recommended Priority 1 command sequence after edits:

```powershell
python -m app.backends.check
python python_app\validate_agentic_workflow.py
python -m pytest -q
python -m pytest tests\test_model_registry.py
python benchmarks\run_benchmark.py --config benchmarks\configs\synthetic_smoke.yaml --output results\synthetic_smoke
python experiments\run_ablation.py --config experiments\ablation_configs\mock_smoke.yaml --output results\mock_ablation
python -m compileall python_app agent segmentation app benchmarks provenance tests contour_io memory
```

## Priority 2

Goal: prepare optional real-backend and benchmark infrastructure without claiming results prematurely.

| Task | Exact files to create or edit | Exact commands to run | Expected outputs | Risk level | User input needed |
|---|---|---|---|---|---|
| Cellpose backend | Edit `segmentation/backends/cellpose_backend.py`, add optional dependency docs/tests gated by env | `python -m app.backends.check`; `RUN_HEAVY_TESTS=1 python -m pytest tests/test_cellpose_backend.py` | Real Cellpose path when installed; OpenCV fallback remains for CI | Medium | Yes for install/GPU choice |
| LangSAM wrapper | Edit `segmentation/backends/langsam_backend.py`; create example external script docs/config | `python -m app.backends.check`; heavy test only when configured | Real or external LangSAM config path; `NOT_CONFIGURED` otherwise | High | Yes for repo/checkpoint |
| MedSAM wrapper | Edit `segmentation/backends/medsam_backend.py`; add bridge config docs | `python -m app.backends.check`; heavy test only when configured | External MedSAM bridge with checkpoint metadata | High | Yes for repo/checkpoint |
| MedSAM2 wrapper | Edit `segmentation/backends/medsam2_backend.py`; add bridge config docs | `python -m app.backends.check`; heavy test only when configured | External MedSAM2 bridge with 3D config metadata | High | Yes for repo/checkpoint |
| Ablation scripts | Extend existing `experiments/run_ablation.py` and configs from mock smoke to real-data dry-run mode | `python experiments/run_ablation.py --config experiments/ablation_configs/mock_smoke.yaml --output results/mock_ablation` | Mock smoke ablation plus real-data `NOT_RUN` guards | Medium | Yes for final data/tasks |
| Export improvements | Wire existing `contour_io` PNG/NIfTI/TIFF/COCO/polygon helpers into `python_app/main.py`; add import round-trips | `python -m pytest tests/test_exporters.py tests/test_importers_and_cli.py` | GUI-accessible exports and round-trip tests | Medium | Yes for required formats |
| Tkinter workflow improvements | Edit `python_app/main.py` to add backend status panel, routing explanation display, memory suggestion display, project save-load, event/provenance logging, and polygon JSON/TIFF/COCO export buttons | GUI smoke test plus `python -m pytest -q` | Current GUI preserved with reviewer-visible reproducibility controls | Medium | No |
| Reviewer quickstart | Edit `docs/reviewer_quickstart.md`, `README.md`; add expected outputs | Run all quickstart commands | 5-10 minute reviewer path | Low | No |

## Priority 3

Goal: support paper artifacts and real studies after Andy supplies datasets, checkpoints, and scope decisions.

| Task | Exact files to create or edit | Exact commands to run | Expected outputs | Risk level | User input needed |
|---|---|---|---|---|---|
| Baseline protocols | Finalize existing `docs/baselines.md` and add raw-output archive checklist | Manual protocol review | Baseline instructions for 3D Slicer, ITK-SNAP, QuPath, native model workflows | Medium | Yes |
| Usability study protocol | Finalize existing `docs/usability_study_protocol.md` and `forms/`; add GUI event logger if study will run | Manual dry run | Study templates without results claims | Medium | Yes |
| Paper assets | Convert existing `paper_assets/` templates into actual figures/tables only after runs | Future figure generation commands from benchmark outputs | Paper-ready outline and placeholder assets | Low | Yes for target journal/title |
| Docker/CI polish | Validate existing `.github/workflows/tests.yml`, `Dockerfile`, `environment.yml`, and `pyproject.toml`; fill metadata | `python -m pytest -q`; Docker build if available | CI and reproducible environments | Medium | Yes for Python/OS/license |
| Real benchmark templates | Extend existing configs and runner to load selected real datasets | `python benchmarks/run_benchmark.py --config benchmarks/configs/medical_3d_template.yaml --output results/real_dry_run` | Dataset-aware benchmark templates with `EXPERIMENT_NOT_RUN` until configured | High | Yes |

## Safest Sequence

1. Add tests and provenance around current lightweight behavior.
2. Make backend availability and routing explanations explicit.
3. Package the lightweight app and document a reviewer quickstart.
4. Add real-backend configs only after checkpoints and environment are known.
5. Add real-data benchmarks only after datasets and ground truth are selected.
6. Add paper claims only after the matching artifact exists.
