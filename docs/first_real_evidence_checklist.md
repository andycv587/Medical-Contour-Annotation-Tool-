# First Real Evidence Checklist

This checklist defines the exact fields required before the first real-data benchmark. Every item must be marked `FILLED`, `NOT_CONFIGURED`, `BLOCKING`, or `OPTIONAL_FOR_FIRST_RUN`.

## A. Microscopy / Cell Benchmark

| item | current status | required value before run |
|---|---|---|
| dataset name | NOT_CONFIGURED | Public dataset name, e.g. Cellpose or BBBC collection. |
| local image directory | BLOCKING | Existing folder containing benchmark images. |
| local mask directory | BLOCKING | Existing folder containing paired ground-truth masks. |
| image pattern | FILLED | `*.png` by default; adjust to `*.tif`, `*.tiff`, or another real pattern. |
| mask pattern | FILLED | `*.png` by default; adjust to match ground-truth files. |
| instance mask format | NOT_CONFIGURED | Confirm binary masks or labeled instance masks. |
| selected target channels | FILLED | `[0, 0]` by default for Cellpose-style channels; change only with dataset evidence. |
| max_cases | FILLED | `10` in answer template; can be reduced for first smoke real run. |
| Cellpose installed or not | NOT_CONFIGURED | Verify with `python -m app.backends.check`; real Cellpose claims require direct Cellpose import, not OpenCV fallback. |
| Cellpose model_type | FILLED | `cyto` by default; set `nuclei` for nuclei-only tasks. |
| output directory | FILLED | `results/real_microscopy_first_run`. |

Minimum first microscopy evidence can be classical-only if `allow_classical_only=true`; it must be reported as a classical baseline, not Cellpose performance.

## B. Medical 3D Benchmark

| item | current status | required value before run |
|---|---|---|
| MSD task name | BLOCKING | Exact MSD task name and target structure. |
| local image directory | BLOCKING | Existing folder containing NIfTI images. |
| local mask directory | BLOCKING | Existing folder containing paired NIfTI masks. |
| target label | FILLED | `1` in answer template; must be confirmed against dataset label map. |
| max_cases | FILLED | `5` in answer template; can be reduced for first smoke real run. |
| MedSAM configured or not | NOT_CONFIGURED | Requires command, checkpoint path, SHA256, source URL, license, and device. |
| MedSAM2 configured or not | NOT_CONFIGURED | Requires command, checkpoint path, SHA256, source URL, license, and device. |
| classical baseline allowed | FILLED | Allowed for first evidence if explicitly reported as classical baseline. |
| oracle bbox prompt enabled or not | FILLED | `true` in answer template; must be disclosed as oracle prompt generation. |
| output directory | FILLED | `results/real_medical_3d_first_run`. |

Oracle bbox/point prompts are permitted only for standardized model evaluation. They are not fully automatic segmentation.

## C. Model Registry

| item | current status | required value before run |
|---|---|---|
| Cellpose enabled true/false | NOT_CONFIGURED | Set true only if real Cellpose should be attempted. |
| LangSAM command | NOT_CONFIGURED | External command or leave disabled. |
| MedSAM command | NOT_CONFIGURED | External command or leave disabled. |
| MedSAM2 command | NOT_CONFIGURED | External command or leave disabled. |
| checkpoint paths | NOT_CONFIGURED | Required for LangSAM/MedSAM/MedSAM2 claims. |
| checkpoint SHA256 | NOT_CONFIGURED | Required for reproducible heavy-backend claims. |
| device | FILLED | `cpu` default; set `cuda:0` only after environment verification. |
| Python executable for external commands | NOT_CONFIGURED | Required if command uses a non-default environment. |

## D. Baseline Evidence

| item | current status | required value before run |
|---|---|---|
| which baseline will be run first | NOT_CONFIGURED | Choose one: 3D Slicer, ITK-SNAP, QuPath, native Cellpose, native MedSAM/MedSAM2, or classical app baseline. |
| exported baseline mask storage | BLOCKING | Existing or planned folder under `baseline_outputs/raw/<baseline_name>/`. |
| timing sheet location | FILLED | `baseline_protocols/baseline_results_template.csv`. |
| raw output archive location | FILLED | `baseline_outputs/raw/`. |

Baseline metrics are `NOT_RUN` until exported masks exist and `python -m app.baselines.evaluate` has been run.
