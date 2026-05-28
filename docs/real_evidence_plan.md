# Real Evidence Plan

This document defines the current evidence boundary for Bioinformatics/Bioinformatics Advances review. It uses strict reviewer-facing language: only commands that have actually run may be described as validated, and only public-dataset experiments that have actually produced outputs may be described as benchmark results.

## 1. Already Validated

- Lightweight editable installation has been validated with `python -m pip install -e .`.
- Core modules compile with `python -m compileall agent app benchmarks contour_io memory provenance segmentation tests experiments`.
- The lightweight test suite has passed with `pytest -q`.
- Backend status reporting runs with `python -m app.backends.check`.
- Synthetic smoke benchmark runs and writes metrics, masks, provenance, routing logs, and report files.
- Provenance inspection runs on the synthetic benchmark session provenance file.
- Mock ablation runs on synthetic smoke cases.
- The legacy headless GUI-adjacent validation script runs on synthetic data and bridge stubs.

These validations demonstrate software execution, routing/provenance plumbing, and CI-safe behavior. They do not establish real biomedical segmentation performance.

## 2. Synthetic/Mock Only

- `results/synthetic_smoke/` is synthetic smoke validation only.
- `results/mock_ablation/` is mock/synthetic ablation only.
- `python_app/validate_agentic_workflow.py` uses synthetic data and included stubs.
- Current Cellpose status is fallback-capable unless real Cellpose is installed.
- Current LangSAM, MedSAM, and MedSAM2 status is unavailable unless external commands or direct installations are configured.

## 3. Missing Real Model Backends

- LangSAM real inference is not configured. Required: external command or stable direct import, source URL, license, checkpoint/model identifier, and reproducible environment.
- MedSAM real inference is not configured. Required: external command, checkpoint path, checkpoint SHA256, source URL, license, and device.
- MedSAM2 real inference is not configured. Required: external command, checkpoint path, checkpoint SHA256, source URL, license, and device.
- Cellpose real inference is not validated in this environment. Required: Cellpose installation and declared model configuration if Cellpose results are claimed.

## 4. Public Datasets Still NOT_CONFIGURED

- Medical 3D: MSD subset is prioritized but exact task, data root, image folder, mask folder, labels, source URL, license, and citation are `NOT_CONFIGURED`.
- Microscopy: Cellpose dataset or BBBC is prioritized but exact collection, data root, image folder, mask folder, mask format, source URL, license, and citation are `NOT_CONFIGURED`.
- Optional datasets such as BTCV, FLARE, MoNuSeg, and CPM remain template-only.

## 5. Files To Edit Before Real Experiments

- `configs/model_registry.local.yaml`: copy from `configs/model_registry.local.template.yaml` and fill real backend entries.
- `configs/datasets.local.yaml`: copy from `configs/datasets.local.template.yaml` and fill public dataset paths/metadata.
- `configs/experiment_registry.local.yaml`: optional copy from `configs/experiment_registry.local.template.yaml` for local run bookkeeping.
- `benchmarks/configs/medical_3d_msd_local.template.yaml`: copy to a local config and set local registry paths/output/max cases/labels.
- `benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml`: copy to a local config and set local registry paths/output/max cases/channel settings.
- `experiments/ablation_configs/medical_3d_router_memory_local.template.yaml`: copy and configure after medical data/backends are available.
- `experiments/ablation_configs/microscopy_backend_memory_local.template.yaml`: copy and configure after microscopy data/backends are available.

Do not commit private local paths if the repository is public.

## 6. Experiments Runnable Immediately

- Lightweight unit/smoke tests.
- Backend availability status report.
- Synthetic smoke benchmark.
- Mock/synthetic ablation.
- Provenance inspection of synthetic smoke outputs.
- Preflight on template configs, which is expected to fail safely and write `results/PREFLIGHT_FAILED.md`.

## 7. Experiments Blocked

- Real medical 3D benchmark is blocked by missing MSD/local dataset paths and real backend/checkpoint configuration if MedSAM/MedSAM2 results are desired.
- Real microscopy benchmark is blocked by missing Cellpose/BBBC/local dataset paths and optional real Cellpose installation if Cellpose results are desired.
- Real router/memory ablations are blocked by real datasets and, for foundation-model claims, real backends.
- Manual baseline comparisons are blocked by operator execution and archived exports from 3D Slicer, ITK-SNAP, QuPath, and native backends.
- Usability/time-study claims are blocked by participant execution and event/result logs.

## 8. Currently Allowed Claims

- The repository provides a lightweight desktop and headless biomedical/bioimage annotation workflow.
- The software includes a common backend interface, transparent router, fallback logging, memory schema, provenance logging, and export/import helpers.
- The lightweight CI path can run without heavy model checkpoints.
- Synthetic smoke tests validate execution of the benchmark/provenance/routing pipeline.
- Real-data benchmark support is prepared through local configuration templates, preflight checks, and dataset loaders.

## 9. Currently Forbidden Claims

- Do not claim real LangSAM, MedSAM, MedSAM2, or Cellpose performance until those backends are actually configured and run.
- Do not claim public-dataset Dice, IoU, Hausdorff95, object F1, runtime, memory benefit, or usability results until outputs are generated from real datasets/studies.
- Do not describe oracle ground-truth-derived prompts as autonomous segmentation.
- Do not claim clinical readiness, diagnostic validity, DICOM SEG/RTSTRUCT support, or SOTA segmentation performance.
- Do not report synthetic/mock smoke values as Bioinformatics benchmark evidence.
