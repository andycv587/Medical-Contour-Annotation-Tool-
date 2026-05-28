# Codex First Real Evidence Readiness Report

Date: 2026-05-03

## 1. What Is Ready

- Lightweight install and tests still pass.
- Synthetic smoke benchmark still runs, with provenance inspect reporting `event_count: 2`.
- Config validation exists and reports `NOT_CONFIGURED` fields without running experiments.
- Preflight exists and safely fails on unfilled templates.
- First-run local answer template exists: `configs/andy_real_run_answers.template.yaml`.
- Local config generator exists: `scripts/create_local_config_from_answers.py`.
- First-run benchmark commands now accept explicit `--models` and `--datasets` overrides.
- Microscopy and medical 3D benchmark paths are guarded against mock use unless explicitly allowed.
- Cellpose OpenCV fallback is blocked from being reported as real Cellpose performance in real-data benchmark mode.
- Real ablation commands accept `--models` and `--datasets` and write `EXPERIMENT_NOT_RUN.md` when blocked.
- Baseline evaluator validates exported mask paths and computes metrics only when real predictions and ground truth exist.

## 2. What Remains NOT_CONFIGURED

- `configs/model_registry.local.yaml`
- `configs/datasets.local.yaml`
- Microscopy dataset name, image directory, mask directory, mask format, and source metadata.
- Medical 3D dataset/MSD task name, image directory, mask directory, target label confirmation, and source metadata.
- Real Cellpose installation status.
- Real LangSAM command/checkpoint/SHA256.
- Real MedSAM command/checkpoint/SHA256.
- Real MedSAM2 command/checkpoint/SHA256.
- Manual/native baseline exported masks.
- Usability study rows.

## 3. Exact Fields Andy Must Fill

Fill `configs/andy_real_run_answers.template.yaml`, then generate local configs.

Microscopy:

- `microscopy.enabled`
- `microscopy.dataset_name`
- `microscopy.images_dir`
- `microscopy.masks_dir`
- `microscopy.image_pattern`
- `microscopy.mask_pattern`
- `microscopy.instance_masks`
- `microscopy.channels`
- `microscopy.max_cases`
- `microscopy.allow_classical_only`

Medical 3D:

- `medical_3d.enabled`
- `medical_3d.dataset_name`
- `medical_3d.images_dir`
- `medical_3d.masks_dir`
- `medical_3d.image_pattern`
- `medical_3d.mask_pattern`
- `medical_3d.target_label`
- `medical_3d.max_cases`
- `medical_3d.oracle_bbox_prompt`
- `medical_3d.allow_classical_only`

Models:

- `models.cellpose.enabled`
- `models.cellpose.model_type`
- `models.cellpose.diameter`
- `models.cellpose.channels`
- `models.cellpose.device`
- `models.langsam.command`
- `models.langsam.checkpoint_path`
- `models.langsam.checkpoint_sha256`
- `models.langsam.device`
- `models.langsam.python_executable`
- `models.medsam.command`
- `models.medsam.checkpoint_path`
- `models.medsam.checkpoint_sha256`
- `models.medsam.device`
- `models.medsam.python_executable`
- `models.medsam2.command`
- `models.medsam2.checkpoint_path`
- `models.medsam2.checkpoint_sha256`
- `models.medsam2.device`
- `models.medsam2.python_executable`

Baseline:

- `baseline_name`
- `dataset_name`
- `case_id`
- `operator_id`
- `input_image_path`
- `ground_truth_mask_path`
- `predicted_mask_path`
- `time_sec`
- `clicks`
- `prompts`
- `corrections`
- `notes`

## 4. Exact Commands After Filling Configs

Generate local configs:

```powershell
python scripts/create_local_config_from_answers.py --answers configs/andy_real_run_answers.template.yaml --output-dir configs
```

Use `--force` only if intentionally overwriting existing local configs.

Validate and preflight:

```powershell
python -m app.configs.validate --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment microscopy
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment medical_3d
```

Run first real benchmarks only after preflight passes:

```powershell
python benchmarks/run_benchmark.py --config benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --output results/real_microscopy_first_run
python benchmarks/run_benchmark.py --config benchmarks/configs/medical_3d_msd_local.template.yaml --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --output results/real_medical_3d_first_run
```

Run real ablation dry paths after configs exist:

```powershell
python experiments/run_ablation.py --config experiments/ablation_configs/microscopy_backend_memory_local.template.yaml --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --output results/real_ablation_microscopy
python experiments/run_ablation.py --config experiments/ablation_configs/medical_3d_router_memory_local.template.yaml --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --output results/real_ablation_medical_3d
```

Evaluate baseline exports:

```powershell
python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir NOT_CONFIGURED --pred-dir NOT_CONFIGURED --output results/baseline_eval
```

## 5. How To Identify Result Type

- Real result: generated from configured public dataset paths, with `dataset_manifest_resolved.json`, `model_registry_resolved.json`, `backend_status.json`, real image/mask paths, and no `EXPERIMENT_NOT_RUN.md`.
- Synthetic result: `benchmark_kind` is `synthetic_smoke` or output directory is `results/synthetic_smoke`.
- Mock result: selected backend is `mock`, or report/result category says `mock backend result`.
- Classical baseline result: selected backend is `classical`; valid as classical baseline only.
- Real Cellpose result: selected backend is `cellpose` and `backend_status.json` shows real Cellpose import, not `mode: opencv-fallback`.
- Oracle-prompt result: `oracle_prompt=true` in `metrics.csv` or report, with disclosure that ground truth was used only to generate standardized prompts.
- Not run: output directory contains `EXPERIMENT_NOT_RUN.md`, `BASELINE_NOT_RUN.md`, `USABILITY_NOT_RUN.md`, or `PREFLIGHT_FAILED.md`.

## 6. Submission Readiness

The current software is not yet submission-ready for Bioinformatics/Bioinformatics Advances results claims. It is engineering-ready for first real evidence collection. Submission readiness still requires at least one configured public microscopy/cell benchmark, one configured 3D medical benchmark or a narrowed scope, baseline evidence, final release metadata, and careful claim boundaries.

## 7. Remaining Bioinformatics Rejection Risks

- Real microscopy benchmark: NOT_RUN.
- Real medical 3D benchmark: NOT_RUN.
- Real backend performance: NOT_RUN.
- Baseline comparison: NOT_RUN.
- Usability study: NOT_RUN.
- Heavy backend reproducibility: NOT_CONFIGURED.
- Release/archive metadata: TO_BE_FILLED.
- Novelty still depends on showing that routing, memory, provenance, and workflow integration help real annotation tasks.

## 8. Commands Run In This Pass

Passed:

```powershell
python -m pip install -e .
python -m compileall agent app benchmarks contour_io memory provenance segmentation tests experiments
pytest -q
python -m app.backends.check
python -m app.configs.validate --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml
python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke
python -m app.provenance.inspect results/synthetic_smoke/provenance/session_provenance.json
python experiments/run_ablation.py --config experiments/ablation_configs/mock_smoke.yaml --output results/mock_ablation
python python_app\validate_agentic_workflow.py
```

Observed:

- `pytest -q`: `37 passed`.
- Preflight on `NOT_CONFIGURED` templates failed safely for both `medical_3d` and `microscopy`.
- No real benchmark result was claimed.
