# Local Model Deployment Report

## Deployment Paths

All new model environments, checkpoints, caches, extracted data, and smoke outputs were placed under:

`D:\Project\Koopman_New\Medical-Contour-Annotation-Tool-`

Key paths:

- MedSAM env: `.model_envs\medsam_env`
- MedSAM repo: `.model_envs\MedSAM`
- MedSAM checkpoint: `.models\MedSAM\medsam_vit_b.pth`
- SAM checkpoint: `.models\SAM\sam_vit_b_01ec64.pth`
- MedSAM2 repo/env: `.model_envs\MedSAM2`, `.model_envs\medsam2_env`
- MedSAM2 checkpoint: `.models\MedSAM2\MedSAM2_latest.pt`
- Cellpose env/cache: `.model_envs\cellpose`, `.model_cache\cellpose\cpsam`
- LangSAM env: `.model_envs\langsam`
- LangSAM/SAM2/GroundingDINO cache: `.model_cache`
- Extracted Task01 smoke case: `.data\Task01_BrainTumour_smoke`
- Processed 3D FLAIR benchmark smoke case: `.data\Task01_BrainTumour_smoke_processed`
- BBBC038 raw microscopy archive: `.data\BBBC038\stage1_train.zip`
- BBBC038 processed microscopy subset: `.data\BBBC038_stage1_train_processed`
- Model smoke outputs: `results\model_deploy_smoke`
- Real-data smoke benchmark: `results\brats457_realdata_smoke`
- BBBC038 microscopy smoke benchmark: `results\bbbc038_microscopy_realdata_smoke`

## Configured Models

- MedSAM: configured and enabled in `configs\model_registry.local.yaml`
  - checkpoint SHA256: `34b34b78c1d18cb8c6bf84cf9c00e135d6d6c965699f3c0e31ef1bc9dcb5be74`
- SAM ViT-B: downloaded and recorded in `configs\model_registry.local.yaml`
  - checkpoint SHA256: `ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912`
- LangSAM: configured and enabled in `configs\model_registry.local.yaml`
  - SAM2.1 small checkpoint SHA256: `6d1aa6f30de5c92224f8172114de081d104bbd23dd9dc5c58996f0cad5dc4d38`
  - GroundingDINO base weights cached under `.model_cache\hf`
- Cellpose: configured and enabled in `configs\model_registry.local.yaml`
  - Cellpose 4.1.1 environment exists at `.model_envs\cellpose`
  - Cellpose-SAM/CPSAM weights cached at `.model_cache\cellpose\cpsam`
  - CPSAM SHA256: `e1440429eb384f95afe32bcba6510f90d518eaedc917ede549bed6804004abe2`
- MedSAM2: repo, environment, checkpoint, and direct CPU propagation bridge are available on D drive.
  - checkpoint SHA256: `c92743b99f00d078bf32a3afcc38aaa9faf1c1692dffe3eaa7a90938c1991060`
  - registry status after direct bridge validation: `CONFIGURED`

## Task01 BrainTumour Smoke Test

Source file:

`Examples\Task01_BrainTumour.tar`

Extracted case:

`BRATS_457`

Original image shape:

`(240, 240, 155, 4)`

Labels:

- 0 background
- 1 edema
- 2 non-enhancing tumor
- 3 enhancing tumour

Representative 2D slice:

- channel: FLAIR
- z: 52
- oracle bbox from label: `[93, 52, 155, 111]`

Direct model bridge smoke outputs:

- MedSAM output: `results\model_deploy_smoke\medsam_mask.npy`, shape `(240, 240)`, nonzero pixels `1814`
- SAM output: `results\model_deploy_smoke\sam_mask.npy`, shape `(240, 240)`, nonzero pixels `2639`
- LangSAM output: `results\model_deploy_smoke\langsam_mask.npy`, shape `(240, 240)`, nonzero pixels `14955`

These are deployment smoke outputs, not publication benchmark claims.

## BBBC038 Microscopy Download And Smoke Test

Downloaded public microscopy data:

`https://data.broadinstitute.org/bbbc/BBBC038/stage1_train.zip`

Local archive:

`.data\BBBC038\stage1_train.zip`

Processed subset:

`.data\BBBC038_stage1_train_processed`

The processed subset contains 10 image/mask pairs. Each original per-object PNG mask was combined into one uint16 instance mask. `configs\datasets.local.yaml` now points microscopy benchmarks to this processed subset with `channel: 0`.

Preflight:

`python -m app.experiments.preflight --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --experiment microscopy --output-dir results\preflight_bbbc038_microscopy`

Result:

Preflight passed with one loaded probe case and available backends `cellpose` and `classical`.

Benchmark:

`python benchmarks\run_benchmark.py --config benchmarks\configs\microscopy_cellpose_or_bbbc_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\bbbc038_microscopy_realdata_smoke`

Result:

Benchmark completed with 5 public BBBC038 microscopy cases using the real Cellpose external backend. Outputs are in `results\bbbc038_microscopy_realdata_smoke`.

This is real public-data smoke evidence, but it is not yet a final publication benchmark because it uses only 5 cases, CPU execution, a single channel, and no baseline/user-study comparison.

## Real-Data Pipeline Smoke

Created a processed 3D FLAIR-only single-case dataset:

`configs\datasets.local.yaml`

Preflight:

`python -m app.experiments.preflight --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --experiment medical_3d --output-dir results\preflight_brats457_smoke`

Result:

Preflight passed with one loaded case and available backends `medsam` and `classical`.

Benchmark:

`python benchmarks\run_benchmark.py --config benchmarks\configs\medical_3d_msd_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\brats457_realdata_smoke`

Result:

Benchmark completed with one historical real-data smoke case before the MedSAM/MedSAM2 volume bridges were added. The router selected classical after the original 2D-only MedSAM bridge failed on 3D input. This older output must not be reported as MedSAM or MedSAM2 performance; use `results\brats457_medsam3d_slice_oracle` and `results\brats457_medsam2_oracle` for the current MedSAM/MedSAM2 smoke evidence.

## MedSAM And MedSAM2 BRATS_457 Ground-Truth Comparison

After adding volume-safe bridges, both MedSAM and MedSAM2 were run against the processed BRATS_457 FLAIR volume with label `3` (enhancing tumour) as ground truth. Both runs used benchmark-only oracle prompts derived from the ground-truth mask. This means ground truth was used only to standardize bbox prompt generation; these runs are not autonomous segmentation.

MedSAM slice-wise volume run:

`python benchmarks\run_benchmark.py --config benchmarks\configs\medical_3d_msd_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\brats457_medsam3d_slice_oracle`

Result:

- selected backend: `medsam`
- processed slices: `25`
- Dice: `0.43597379392495533`
- IoU: `0.27875095201827876`
- precision: `0.6036283672347443`
- recall: `0.34120571783716597`
- HD95: `4.123105625617661`
- runtime: `158.6211020000046` seconds on CPU

MedSAM2 propagation run:

`python benchmarks\run_benchmark.py --config benchmarks\configs\medical_3d_msd_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\brats457_medsam2_oracle`

Result:

- selected backend: `medsam2`
- processed slices: `26`
- Dice: `0.20994420087684337`
- IoU: `0.11728360701363763`
- precision: `0.12501483327400023`
- recall: `0.6547545059042884`
- HD95: `30.740852297878796`
- runtime: `25.000165400037076` seconds on CPU

MedSAM2 emitted the expected warning that the optional SAM2 CUDA post-processing extension is not built in this CPU environment. The run still completed and wrote masks, routing logs, metrics, and provenance.

## Verification

- `python -m compileall scripts segmentation app tests benchmarks`: passed after fixes
- `pytest -q`: `38 passed`
- `python -m app.backends.check`: reads `configs\model_registry.local.yaml` and reports MedSAM/LangSAM external commands available
- `python -m app.configs.validate --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml`: schema valid
- `python -m app.experiments.preflight --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --experiment microscopy --output-dir results\preflight_bbbc038_microscopy`: passed
- `python benchmarks\run_benchmark.py --config benchmarks\configs\microscopy_cellpose_or_bbbc_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\bbbc038_microscopy_realdata_smoke`: passed, 5 cases
- `python benchmarks\run_benchmark.py --config benchmarks\configs\medical_3d_msd_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\brats457_medsam3d_slice_oracle`: passed, MedSAM selected
- `python benchmarks\run_benchmark.py --config benchmarks\configs\medical_3d_msd_local.template.yaml --models configs\model_registry.local.yaml --datasets configs\datasets.local.yaml --output results\brats457_medsam2_oracle`: passed, MedSAM2 selected

## Important Claim Boundary

Allowed:

- MedSAM, SAM, and LangSAM are locally deployed on D drive.
- Cellpose and its CPSAM weights are locally deployed on D drive.
- MedSAM2 repo/env/checkpoint are downloaded on D drive and direct CPU propagation bridge has been validated on a tiny smoke volume and BRATS_457.
- MedSAM/SAM/LangSAM bridge smoke inference ran on a real slice from `Task01_BrainTumour.tar`.
- MedSAM and MedSAM2 ran against BRATS_457 enhancing-tumor ground truth using oracle bbox prompts.
- A 5-case BBBC038 real microscopy smoke benchmark ran with the real Cellpose external backend.
- One real-data pipeline smoke benchmark ran on the processed BRATS_457 FLAIR volume.

Forbidden:

- Do not claim MedSAM 3D benchmark performance.
- Do not claim MedSAM/MedSAM2 autonomous performance from the BRATS_457 runs because oracle prompts were used.
- Do not claim full MedSAM2 clinical-grade performance from one CPU smoke case.
- Do not claim full MSD Task01 results.
- Do not use the one-case smoke numbers as publication evidence.
- Do not treat the 5-case BBBC038 smoke run as a complete publication benchmark.
