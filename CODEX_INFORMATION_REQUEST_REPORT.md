# Codex Information Request Report

Audit date: 2026-05-03

## 1. What I Inspected

- Repository root, tracked/untracked file structure, and placeholder directories.
- `README.md` and `docs/repo_audit.md`.
- Tkinter GUI implementation in `python_app/main.py`.
- GUI-facing agents and router in `python_app/ai_agents.py`.
- Geometry memory in `python_app/agent_memory.py`.
- Deterministic LangSAM/MedSAM/MedSAM2 bridge stubs.
- Headless synthetic validation script.
- Newer backend API under `segmentation/backends/`.
- Newer workflow/router API under `agent/`.
- Backend checker under `app/backends/check.py`.
- Package/release scaffolding: `pyproject.toml`, root `requirements.txt`, `environment.yml`, `Dockerfile`, `Makefile`, `.github/workflows/tests.yml`, `LICENSE`, `CITATION.cff`, `INSTALL.md`, `ENVIRONMENT.md`, `CHANGELOG.md`.
- Benchmark, ablation, provenance, contour IO, memory, forms, and paper asset scaffolds.
- Existing tests, benchmark, provenance, paper asset, documentation, and config directories.

I also ran:

```powershell
python -m app.backends.check
python python_app\validate_agentic_workflow.py
python -m compileall python_app agent segmentation app
python -m pytest -q
python benchmarks\run_benchmark.py --config benchmarks\configs\synthetic_smoke.yaml --output results\synthetic_smoke_audit
python experiments\run_ablation.py --config experiments\ablation_configs\mock_smoke.yaml --output results\mock_ablation_audit
```

`python -m pytest -q` passed 17 tests. The synthetic benchmark and mock ablation runner completed locally. A direct parallel provenance inspect initially raced the benchmark output, then succeeded when rerun after the benchmark completed.

## 2. What Is Currently Implemented

- Tkinter GUI for loading 3D NIfTI and 2D/multi-page image files.
- Manual polygon annotation with labels, colors, layers, selection, undo/redo, preview/apply behavior.
- PNG and NIfTI mask export from committed masks.
- Classical watershed and levelset-like segmentation in the GUI.
- Built-in OpenCV CellSeg path for microscopy/cell-like segmentation.
- GUI-facing AgenticWorkflow router with heuristic routing and optional external router command.
- LangSAM, MedSAM, and MedSAM2 external bridge protocols with deterministic stubs.
- Short-term and long-term geometry memory storing prompts, bboxes, timings, and metadata rather than raw voxels.
- Newer backend interface and workflow/router modules, currently not fully unified with the GUI path.
- Synthetic validation script that passes locally with deterministic stubs.
- Lightweight package scaffold with editable-install metadata.
- Pytest suite for router, backends, exporters/importers, memory, provenance, and synthetic benchmark execution.
- CI workflow file for editable install, tests, and synthetic benchmark.
- Synthetic benchmark runner with metrics, routing logs, mask exports, figures, report, and provenance.
- Mock smoke ablation runner and real-ablation templates.
- Reusable contour IO helpers for PNG, NIfTI, TIFF stack, polygon JSON, and COCO JSON.
- Provenance logger and inspect CLI for headless benchmark outputs.
- Paper outline, result table placeholders, baseline protocols, usability-study templates, availability placeholder, and reproducibility checklist.

## 3. What Is Missing

- Clean-environment install verification and remote CI status.
- Final package metadata, author/copyright/repository fields, release tag, archive, and DOI.
- Selected real public dataset manifests, sample data, local paths, and ground-truth masks.
- Real-data benchmark execution; current real-data configs are templates and guarded as not run.
- Baseline comparison results; protocol templates exist.
- Real ablation results; mock smoke and templates exist.
- Full GUI session/export provenance integration.
- Paper-ready figures and filled quantitative tables; current assets are placeholders.
- Real LangSAM, MedSAM, MedSAM2, Cellpose, or micro-SAM backend configuration/checkpoints in this environment.
- Checkpoint registry with paths, versions, licenses, and checksums.
- OME-TIFF, DICOM SEG, and RTSTRUCT implementation. DICOM/RTSTRUCT are currently documented as limitations/future work.
- Clean-environment reviewer quickstart validation with exact expected outputs.

## 4. What Questions Andy Needs To Answer

Andy has answered the first decision round. The decisions are recorded in `docs/project_decisions.md`, and the remaining open questions are in `docs/questions_for_andy.md`.

The main remaining blockers are:

- exact MSD subset/task and Cellpose/BBBC collection;
- local dataset paths and ground-truth mask locations;
- real external bridge commands;
- checkpoint paths, versions, source URLs, licenses, and SHA256 checksums for the model registry;
- manual baseline operators and archived output locations;
- final GitHub URL, copyright holder, release tag, and Zenodo DOI.

## 5. What Can Be Implemented Immediately

- GUI integration for the existing provenance logger.
- Reconciliation/documentation of the two memory layers.
- Formal backend availability checker expected output in README/reviewer docs.
- Session provenance JSONL logger.
- Router explanation display/logging.
- Clean-environment verification of install/tests/benchmark/Docker/conda.
- GUI integration of existing contour IO exports beyond PNG/NIfTI.
- Dataset and model config schemas with `NOT_CONFIGURED` defaults.
- Paper figure scaffolds for architecture and workflow diagrams.

## 6. What Must Wait

- Real benchmark results must wait for datasets, paths, labels, and privacy/license decisions.
- Real LangSAM/MedSAM/MedSAM2/Cellpose/micro-SAM claims must wait for installed backends, checkpoint paths, and heavy integration tests.
- Baseline results must wait for selected baselines and operators.
- Usability/time study results must wait for participants, tasks, and study protocol decisions.
- License, DOI/archive, final title, and availability statement must wait for Andy's decisions.

## 7. Safest Next Implementation Sequence

1. Consolidate/document the backend, workflow, and memory interfaces.
2. Wire provenance and route explanations into GUI actions/exports.
3. Clean-env verify package install, tests, synthetic benchmark, mock ablation, Docker/conda, and CI.
4. Fill package/license/citation metadata after Andy confirms author/repo/license.
5. Add real dataset/checkpoint config schemas with safe `NOT_CONFIGURED` defaults.
6. Add real-backend configs after checkpoints and environment are provided.
7. Add real benchmark and baseline scripts after datasets and baselines are chosen.
8. Generate paper assets only with `NOT_RUN` placeholders until experiments actually run.

## 8. Highest Bioinformatics Rejection Risks

- The software may be viewed as wrapper/glue code unless routing, memory, provenance, and reproducibility are tested and clearly positioned.
- No real-data benchmark currently exists.
- No baseline comparison currently exists.
- Heavy model integrations are currently stubs/bridges or unavailable in this environment.
- Installation, license, citation, and CI scaffolding exist but still contain placeholders or need validation; archive/DOI is missing.
- Bioinformatics scope may be weak unless microscopy/cell/bioimage use cases and datasets are prioritized.
- Unsupported claims would be a serious risk; synthetic smoke results must not be presented as real benchmark performance.
