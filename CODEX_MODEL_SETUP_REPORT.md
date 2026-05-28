# Model Setup Report

## Local Model Environments

Created optional isolated model environments under `.model_envs/`:

- Cellpose: `.model_envs/cellpose`
- LangSAM: `.model_envs/langsam`
- MedSAM repository: `.model_envs/MedSAM`
- MedSAM environment: `.model_envs/medsam_env`
- MedSAM2 repository: `.model_envs/MedSAM2`
- MedSAM2 environment: `.model_envs/medsam2_env`

These environments do not replace the lightweight package environment.

## Local Configs

Generated local, gitignored configs:

- `configs/andy_real_run_answers.local.yaml`
- `configs/model_registry.local.yaml`
- `configs/datasets.local.yaml`
- `configs/experiment_registry.local.yaml`

Cellpose is enabled through an external command bridge. LangSAM, MedSAM, and MedSAM2 have real local commands/repo paths recorded but remain disabled until checkpoint paths and SHA256 values are filled.

## Bridge Status

- `scripts/model_bridges/cellpose_bridge.py`: smoke-tested. It runs, writes an output mask, and downloaded/cache-initialized upstream Cellpose model assets. The toy smoke image produced an empty mask, so this is not a segmentation-quality result.
- `scripts/model_bridges/langsam_bridge.py`: import smoke passed in `.model_envs/langsam`.
- `scripts/model_bridges/medsam_bridge.py`: dependency import smoke passed through `segment_anything`; a real MedSAM checkpoint is still required.
- `scripts/model_bridges/medsam2_bridge.py`: command-contract bridge only; a site-specific MedSAM2 upstream adapter/checkpoint is still required before real inference.

## Validation

- `pytest -q`: 38 passed.
- `python -m app.configs.validate --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml`: schema valid; datasets and heavy checkpoints remain `NOT_CONFIGURED`.
- Local preflight for microscopy sees Cellpose external command and classical backend, then fails safely because dataset paths are still `NOT_CONFIGURED`.
- Real benchmark commands fail safely with `EXPERIMENT_NOT_RUN.md` until dataset paths are filled.

No real public-dataset benchmark has been run. No real model performance should be claimed yet.
