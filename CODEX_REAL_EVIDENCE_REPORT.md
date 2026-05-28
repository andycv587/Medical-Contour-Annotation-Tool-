# Codex Real Evidence Readiness Report

Date: 2026-05-03

## Summary

The repository has moved from publication scaffold to real-evidence readiness. It now has local configuration templates, schema validation, real-experiment preflight, paired real-dataset loaders, benchmark guardrails, baseline evaluation protocols, usability/event logging readiness, and paper asset claim boundaries.

No real public-dataset benchmark has been run in this environment. No real LangSAM, MedSAM, MedSAM2, or Cellpose performance is claimed.

## What Is Ready For Real Experiments

- Local model registry template: `configs/model_registry.local.template.yaml`.
- Local dataset registry template: `configs/datasets.local.template.yaml`.
- Local experiment registry template: `configs/experiment_registry.local.template.yaml`.
- Config validation CLI: `python -m app.configs.validate`.
- Real preflight CLI: `python -m app.experiments.preflight`.
- Medical 3D paired NIfTI loader with shape validation, label extraction, max cases, affine/spacing/orientation metadata.
- Microscopy paired image/mask loader with PNG/TIFF/JPEG support, channel selection, instance-mask flag, max cases, and shape validation.
- Real benchmark templates:
  - `benchmarks/configs/medical_3d_msd_local.template.yaml`
  - `benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml`
- Real benchmark runner guardrails:
  - blocks missing registries;
  - blocks requested heavy backends marked `NOT_CONFIGURED`;
  - blocks mock backend when `allow_mock_backend=false`;
  - writes `EXPERIMENT_NOT_RUN.md` instead of fabricating results;
  - records `oracle_prompt=true` for ground-truth-derived prompt benchmarks.
- Real ablation templates:
  - `experiments/ablation_configs/medical_3d_router_memory_local.template.yaml`
  - `experiments/ablation_configs/microscopy_backend_memory_local.template.yaml`
- Baseline execution package under `baseline_protocols/` plus `python -m app.baselines.evaluate`.
- GUI usability/event logger support through `provenance/gui_logger.py` and existing Tkinter event hooks.
- Usability result template and analysis placeholder:
  - `forms/usability_results_template.csv`
  - `scripts/analyze_usability_results.py`
- Claim-boundary docs:
  - `docs/real_evidence_plan.md`
  - `docs/reject_risk_audit.md`

## What Remains NOT_CONFIGURED

- `configs/model_registry.local.yaml` does not exist yet.
- `configs/datasets.local.yaml` does not exist yet.
- LangSAM real command/checkpoint/source/license/SHA256 are not configured.
- MedSAM real command/checkpoint/source/license/SHA256 are not configured.
- MedSAM2 real command/checkpoint/source/license/SHA256 are not configured.
- Real Cellpose direct-import run is not validated here.
- MSD task/data root/image and mask folders/target label are not configured.
- Cellpose/BBBC microscopy data root/image and mask folders are not configured.
- Manual baseline exports are not available.
- Usability study rows are not available.

## Commands Andy Must Run After Filling Local Configs

Copy templates:

```powershell
Copy-Item configs/model_registry.local.template.yaml configs/model_registry.local.yaml
Copy-Item configs/datasets.local.template.yaml configs/datasets.local.yaml
```

Fill real paths, checksums, source URLs, licenses, citations, labels, and dataset folders. Then run:

```powershell
python -m app.configs.validate --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment medical_3d
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment microscopy
```

Only after preflight passes:

```powershell
python benchmarks/run_benchmark.py --config benchmarks/configs/medical_3d_msd_local.yaml --output results/medical_3d_msd
python benchmarks/run_benchmark.py --config benchmarks/configs/microscopy_cellpose_or_bbbc_local.yaml --output results/microscopy_cellpose_or_bbbc
```

For baselines after exported masks exist:

```powershell
python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir <ground_truth_dir> --pred-dir <baseline_prediction_dir> --output results/baseline_eval/<baseline_name>
```

For usability after pilot rows exist:

```powershell
python scripts/analyze_usability_results.py --input forms/usability_results_template.csv --output results/usability
```

## Outputs That Will Be Publication Evidence

Only after real data/backends are configured and preflight passes:

- `results/<real_benchmark>/metrics.csv`
- `results/<real_benchmark>/per_case_results.jsonl`
- `results/<real_benchmark>/routing_decisions.jsonl`
- `results/<real_benchmark>/backend_status.json`
- `results/<real_benchmark>/dataset_manifest_resolved.json`
- `results/<real_benchmark>/model_registry_resolved.json`
- `results/<real_benchmark>/provenance/`
- `results/<real_benchmark>/masks/`
- `results/<real_benchmark>/report.md`
- `results/baseline_eval/<baseline>/baseline_metrics.csv`
- completed usability CSV rows and `results/usability/usability_summary.md`

## Outputs That Remain Smoke-Only

- `results/synthetic_smoke/`
- `results/mock_ablation/`
- outputs from `python_app/validate_agentic_workflow.py`

These validate code paths only. They are not real Bioinformatics benchmark results.

## Required Commands Run In This Environment

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

- `pytest -q`: `34 passed`.
- Provenance inspect reported `event_count: 2` after fixing benchmark session overwrite.
- `python -m app.backends.check` shows mock/classical available, Cellpose fallback available, and LangSAM/MedSAM/MedSAM2 not configured.

Expected safe failures:

```powershell
python -m app.experiments.preflight --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml --experiment medical_3d
python -m app.experiments.preflight --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml --experiment microscopy
```

Both preflight commands failed safely because dataset paths are `NOT_CONFIGURED`; `results/PREFLIGHT_FAILED.md` was written. No benchmark was run and no results were fabricated.

## Claim Boundary

Allowed now:

- The software has a reproducible lightweight installation and test path.
- The software has a real-experiment readiness layer with config validation, preflight checks, real-data loaders, and benchmark guardrails.
- The router, memory, provenance, export, benchmark, ablation, baseline protocol, and usability logging scaffolds are implemented.

Forbidden now:

- Public-dataset segmentation accuracy/runtime claims.
- Real LangSAM/MedSAM/MedSAM2/Cellpose performance claims.
- Claims that oracle ground-truth prompts are autonomous segmentation.
- Baseline superiority claims.
- User-study efficiency/usability claims.
- Clinical or diagnostic readiness claims.

## Evidence Status After Real-Evidence Readiness

| Evidence class | Status |
|---|---|
| Engineering evidence | DONE |
| Synthetic smoke validation | DONE |
| Config validation | DONE |
| Preflight safety | DONE |
| Real microscopy benchmark | NOT_RUN |
| Real 3D benchmark | NOT_RUN |
| Real backend performance | NOT_RUN |
| Baseline comparison | NOT_RUN |
| Usability study | NOT_RUN |

## Submission Blockers

- Fill release metadata, authorship, repository URL, license holder, Zenodo DOI, and documentation URL.
- Configure at least one public medical 3D dataset and one public microscopy/cell dataset.
- Configure real heavy backends if foundation-model claims are included.
- Run preflight successfully before real benchmarks.
- Run and archive baseline protocol outputs.
- Run or remove usability-study claims.
- Fill paper tables only from generated real outputs; keep all unavailable values as `NOT_RUN`.
