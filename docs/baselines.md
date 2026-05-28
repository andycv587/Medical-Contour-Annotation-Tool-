# Baseline Comparison Protocols

No GUI-based baseline results are claimed unless the protocol below is run and raw outputs are archived.

Detailed task sheets and a results template are in `baseline_protocols/`.

Evaluate exported baseline masks only after real paths exist:

```powershell
python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir NOT_CONFIGURED --pred-dir NOT_CONFIGURED --output results/baseline_eval
```

If paths are `NOT_CONFIGURED`, the evaluator writes `BASELINE_NOT_RUN.md`.

## 3D Slicer Segment Editor

- Task: segment the same target structures used by the benchmark dataset.
- Timing: start when image is loaded; stop when mask export completes.
- Corrections: count manual edits after initial model/classical operation.
- Export: NIfTI labelmap or segmentation converted to NIfTI.
- Metrics: compute Dice/IoU/Hausdorff95 using `benchmarks/metrics.py`.

## ITK-SNAP

- Task: manual contouring or active-contour-assisted segmentation on the same NIfTI volumes.
- Timing: start after volume is opened; stop after segmentation is saved.
- Corrections: count seed edits, parameter restarts, and manual contour corrections.
- Export: NIfTI segmentation image.
- Metrics: Dice/IoU/Hausdorff95 against reference masks.

## QuPath

- Task: cell/tissue detection on the same microscopy/pathology images.
- Timing: start after project/image open; stop after object/mask export.
- Corrections: count manual object edits or classifier retraining iterations.
- Export: GeoJSON, mask image, or object measurements; convert to mask for metrics.
- Metrics: binary Dice/IoU and object precision/recall/F1.

## Cellpose / Cellpose-SAM

- Runnable wrapper: `segmentation.backends.cellpose_backend.CellposeBackend`.
- Config: `diameter`, `channels`, `model_type`, `flow_threshold`, `cellprob_threshold`.
- Export: instance mask TIFF.
- Metrics: object precision/recall/F1; AJI is currently a TODO.

## Micro-SAM

- Status: protocol placeholder.
- Use the official napari plugin or CLI if installed.
- Export masks as TIFF/PNG and evaluate with benchmark metrics.

## MedSAM / MedSAM2 Native Workflow

- Use upstream inference scripts with the same bbox/seed prompts.
- Record checkpoint path/hash, command line, device, and runtime.
- Export NIfTI/TIFF masks and evaluate with the same metrics.

## LangSAM Native Workflow

- Use upstream `lang_sam` package or CLI with the same text prompts.
- Record model/checkpoint versions, prompt text, and runtime.
- Export binary masks and evaluate with the same metrics.
