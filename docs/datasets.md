# Dataset Plan

This project uses public datasets only. Large datasets are not committed to the repository.

## Priority Datasets

| Area | Priority dataset | Status | Notes |
|---|---|---|---|
| 3D biomedical/medical volumes | MSD subset | `NOT_CONFIGURED` | First real 3D benchmark target. Record exact task, version, URL, license, local path, and labels before running. |
| Microscopy/cell/nuclei | Cellpose dataset or BBBC | `NOT_CONFIGURED` | First real bioimage benchmark target. Record exact collection, version, URL, license, local path, and mask format before running. |

## Optional Dataset Templates

| Area | Optional datasets | Status |
|---|---|---|
| 3D biomedical/medical volumes | BTCV, FLARE | `TEMPLATE_ONLY_NOT_RUN` |
| Microscopy/cell/nuclei | MoNuSeg, CPM | `TEMPLATE_ONLY_NOT_RUN` |

## Required Manifest Fields

Every real benchmark dataset must have a manifest with:

- dataset name;
- dataset version or release date;
- official source URL;
- license/terms;
- local `data_root`;
- image glob;
- ground-truth mask glob;
- target labels/classes;
- train/validation/test split used;
- preprocessing assumptions;
- citation.

## Current Policy

- Real benchmark metrics remain `NOT_RUN` until local paths and ground-truth masks are configured.
- Synthetic benchmark outputs are CI/smoke-only and are not publication performance claims.
- No patient-identifiable or private data should be committed, logged, or included in paper screenshots.

## Local Configuration

Copy `configs/datasets.local.template.yaml` to `configs/datasets.local.yaml` and fill only real public dataset paths and metadata. Validate without running experiments:

```powershell
python -m app.configs.validate --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.yaml
```

Run preflight before benchmark execution:

```powershell
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment medical_3d
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment microscopy
```
