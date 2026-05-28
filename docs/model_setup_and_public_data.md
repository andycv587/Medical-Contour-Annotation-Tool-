# Model Setup And Public Dataset Sources

This document records official/open model sources and public dataset candidates. It does not claim that any model or dataset has been run locally.

## Model Backends

| backend | upstream | install path | checkpoint status |
|---|---|---|---|
| Cellpose | https://github.com/MouseLand/cellpose | `python -m pip install cellpose` | built-in pretrained models; cache/download handled by Cellpose |
| LangSAM | https://github.com/luca-medeiros/lang-segment-anything | `pip install -U git+https://github.com/luca-medeiros/lang-segment-anything.git` | SAM/GroundingDINO assets may auto-download or be configured explicitly |
| MedSAM | https://github.com/bowang-lab/MedSAM | clone upstream and install in isolated env | official checkpoint required; record path and SHA256 |
| MedSAM2 | https://github.com/bowang-lab/MedSAM2 | clone upstream and install in isolated env | official checkpoint required; record path and SHA256 |

Windows helper:

```powershell
.\scripts\setup_model_envs.ps1 -Cellpose
.\scripts\setup_model_envs.ps1 -LangSAM
.\scripts\setup_model_envs.ps1 -MedSAM
.\scripts\setup_model_envs.ps1 -MedSAM2
```

The helper defaults to CPU PyTorch wheels. Add `-Torch cu124` if this machine has a compatible CUDA 12.4 setup and you want GPU wheels, for example:

```powershell
.\scripts\setup_model_envs.ps1 -Cellpose -LangSAM -Torch cu124
```

Use `-All` only if you are ready for large downloads and PyTorch dependency resolution. Keep these dependencies in isolated `.model_envs/` environments.

The helper prints the exact bridge command to paste into `configs/model_registry.local.yaml`, for example:

```yaml
models:
  cellpose:
    enabled: true
    backend_mode: external_command
    command: "\"D:\\Project\\...\\.model_envs\\cellpose\\Scripts\\python.exe\" \"D:\\Project\\...\\scripts\\model_bridges\\cellpose_bridge.py\""
```

Available bridge scripts:

- `scripts/model_bridges/cellpose_bridge.py`: real Cellpose execution if Cellpose is importable in that environment.
- `scripts/model_bridges/langsam_bridge.py`: real LangSAM execution if LangSAM and its model assets are available.
- `scripts/model_bridges/medsam_bridge.py`: MedSAM 2D bbox execution using the upstream MedSAM/SAM predictor and a real checkpoint.
- `scripts/model_bridges/medsam2_bridge.py`: command-contract bridge for MedSAM2; it still requires a site-specific `MEDSAM2_UPSTREAM_CMD` adapter before real inference.

Do not report a backend as real unless `backend_status.json` and per-case provenance show that the real backend command ran successfully.

## Recommended First Datasets

### Medical 3D

| dataset | task | source | license/status |
|---|---|---|---|
| Medical Segmentation Decathlon | 10 3D medical segmentation tasks, including liver/spleen/pancreas/etc. | https://medicaldecathlon.com/ | CC-BY-SA 4.0 according to official site/publication |
| KiTS23 | kidney/tumor/cyst CT segmentation | https://kits-challenge.org/ and https://github.com/neheller/kits23 | CC BY-NC-SA 4.0 according to official challenge/repo |
| KiTS19 | kidney/tumor CT segmentation | https://github.com/neheller/kits19 | public challenge dataset; verify license/terms before publication |
| LiTS | liver/liver tumor CT segmentation | https://www.lits-challenge.com/ | public challenge; verify current terms before publication |

### Microscopy / Cell / Nuclei

| dataset | task | source | license/status |
|---|---|---|---|
| BBBC038 / Kaggle 2018 Data Science Bowl | diverse nuclei instance segmentation | https://bbbc.broadinstitute.org/BBBC038 | BBBC-hosted; verify per-image-set terms |
| BBBC image sets | microscopy segmentation/identification tasks | https://bbbc.broadinstitute.org/image_sets | freely downloadable; licenses vary by image set |
| Cellpose training dataset | generalist cellular segmentation | https://www.cellpose.org/dataset | requires accepting HHMI terms |
| MoNuSeg | multi-organ pathology nuclei segmentation | https://monuseg.grand-challenge.org/Data/ | CC BY-NC-SA 4.0 according to challenge page |
| BBBC019 | bright-field collective cell migration segmentation | https://bbbc.broadinstitute.org/BBBC019/ | CC BY 3.0 according to BBBC019 page |

## First-Run Recommendation

Start with:

1. Microscopy: BBBC038 or BBBC019 if you want small, easy public data.
2. Medical 3D: MSD Task09 Spleen or Task03 Liver if you want NIfTI labels that match the current loader style.

After downloading, fill `configs/andy_real_run_answers.template.yaml`, generate local configs, run preflight, and only then run benchmarks.
