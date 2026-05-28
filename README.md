# Medical Contour Annotation Tool

An agent-routed and memory-augmented annotation workflow for biomedical and bioimage segmentation.

This repository contains a lightweight Tkinter desktop annotator plus headless benchmarking utilities. The intended software-paper contribution is not another segmentation GUI, but a reproducible workflow that combines:

- language-guided prompting through LangSAM-compatible bridges
- 2D medical bbox prompting through MedSAM-compatible bridges
- 3D volume propagation through MedSAM2-compatible bridges
- microscopy/cell segmentation through Cellpose when available, with a lightweight fallback
- classical watershed/levelset baselines
- transparent agentic routing and fallback logs
- short-term and long-term prompt/mask geometry memory
- provenance sidecars for exported masks
- headless synthetic smoke benchmarks and real-dataset templates

No benchmark numbers in this repository are fabricated. Synthetic smoke results are only for validation of the software path; real public-dataset experiments require user-provided data and checkpoints.

## Quick Start

Lightweight install:

```powershell
python -m pip install -e .
```

Run tests:

```powershell
make test
```

If GNU Make is unavailable on Windows, run `pytest -q` directly.

Run the synthetic headless benchmark:

```powershell
make benchmark-smoke
```

If GNU Make is unavailable on Windows, run the benchmark command shown in the Headless Benchmark section.

Check backend availability:

```powershell
python -m app.backends.check
```

Optional model setup helpers and public dataset links are documented in [Model setup and public data](docs/model_setup_and_public_data.md). The Windows helper keeps heavy backend dependencies isolated under `.model_envs/`:

```powershell
.\scripts\setup_model_envs.ps1 -Cellpose
.\scripts\setup_model_envs.ps1 -LangSAM -Torch cu124
.\scripts\setup_model_envs.ps1 -MedSAM2 -Torch cu124
```

Validate local real-evidence templates without running experiments:

```powershell
python -m app.configs.validate --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml
```

Generate local config files from an answer template:

```powershell
python scripts/create_local_config_from_answers.py --answers configs/andy_real_run_answers.template.yaml --output-dir configs
```

The generator refuses to overwrite existing `*.local.yaml` files unless `--force` is passed.

Launch the GUI:

```powershell
python python_app\main.py
```

Run the lightweight reviewer verification script:

```powershell
python scripts/verify_lightweight_install.py
```

On Windows, the legacy launcher is still available:

```powershell
python_app\run_python_app.bat
```

## Repository Map

- `python_app/`: existing Tkinter GUI and legacy app bridges
- `segmentation/backends/`: common backend API and LangSAM, MedSAM, MedSAM2, Cellpose, classical, mock backends
- `agent/`: deterministic routing rules, transparent routing decisions, fallback workflow
- `memory/`: schema and store for prompt/geometry/result memory without raw image pixels by default
- `provenance/`: run-level provenance schema, sidecar writer, session logger, inspect CLI
- `contour_io/`: mask, contour, COCO, NIfTI, and TIFF export/import helpers
- `benchmarks/`: headless benchmark runner, metrics, synthetic data, real-dataset templates
- `experiments/`: ablation runner and configs
- `docs/`: reviewer quickstart, baseline protocols, reproducibility checklist, limitations
- `paper_assets/`: table, figure, and software note templates with `NOT_RUN` placeholders where needed

## Backend Modes

### Lightweight Mode

The default install avoids heavy model dependencies and checkpoints. It supports:

- mock backend for CI and tests
- classical watershed/levelset backend
- Cellpose-style microscopy fallback when Cellpose is not installed
- external command wrappers for LangSAM, MedSAM, and MedSAM2 that fail gracefully if not configured

### Full Model Mode

Install optional dependencies and configure checkpoint/command paths:

```powershell
make install-heavy
```

Useful environment variables:

- `LANGSAM_INFER_CMD`: external LangSAM bridge command
- `MEDSAM_INFER_CMD`: external MedSAM bridge command
- `MEDSAM2_INFER_CMD`: external MedSAM2 bridge command
- `MEDSAM_CHECKPOINT`: MedSAM checkpoint path
- `MEDSAM2_CHECKPOINT`: MedSAM2 checkpoint path
- `SEGMENTATION_DEVICE`: `cpu`, `cuda`, or backend-specific value
- `MEMORY_STORE_PATH`: optional long-term memory JSON path
- `RUN_HEAVY_TESTS=1`: enable tests that require real model assets

The external bridge protocol uses `.npy` image inputs, JSON request files, and `.npy` mask outputs. The included wrappers report missing dependencies and checkpoints instead of crashing the GUI or benchmark runner.

## Headless Benchmark

Synthetic smoke benchmark:

```powershell
python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke
```

Expected outputs:

- `metrics.csv`
- `per_case_results.jsonl`
- `backend_status.json`
- `routing_decisions.jsonl`
- `provenance/`
- `masks/`
- `figures/`
- `report.md`

Real-dataset templates are provided for medical 3D and microscopy benchmarks:

- `benchmarks/configs/medical_3d_template.yaml`
- `benchmarks/configs/microscopy_template.yaml`
- `benchmarks/configs/medical_3d_msd_local.template.yaml`
- `benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml`

These templates intentionally do not auto-download large datasets. Provide dataset paths and model checkpoints before using them for paper results.

Run preflight before real-data benchmarks:

```powershell
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment medical_3d
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment microscopy
```

Preflight on unedited templates is expected to fail safely and write `results/PREFLIGHT_FAILED.md`.

## Validation

Run the legacy GUI-adjacent validation script:

```powershell
python python_app\validate_agentic_workflow.py
```

Run package tests:

```powershell
pytest -q
```

Heavy tests must be marked with `@pytest.mark.heavy` and are skipped unless:

```powershell
$env:RUN_HEAVY_TESTS = "1"
```

## Documentation For Reviewers

- [Reviewer quickstart](docs/reviewer_quickstart.md)
- [Repository audit](docs/repo_audit.md)
- [Reproducibility checklist](docs/reproducibility_checklist.md)
- [Availability statement template](docs/availability_statement.md)
- [Baseline comparison protocol](docs/baselines.md)
- [Usability study protocol](docs/usability_study_protocol.md)
- [DICOM/RTSTRUCT limitations](docs/dicom_rtstruct_limitations.md)
- [Benchmark README](benchmarks/README.md)
- [Ablation README](experiments/README.md)
- [Software note outline](paper_assets/software_note_outline.md)

## Current Limitations

- Real LangSAM, MedSAM, and MedSAM2 inference requires external installations/checkpoints or bridge commands.
- Public-dataset benchmark results are not included and must be run by the authors.
- DICOM SEG and RTSTRUCT export are documented as future work, not claimed as implemented.
- Synthetic smoke outputs demonstrate software execution only; they are not evidence of real biomedical segmentation accuracy.

## License And Citation

See `LICENSE` and `CITATION.cff`. Fill the remaining project metadata placeholders before public release.
