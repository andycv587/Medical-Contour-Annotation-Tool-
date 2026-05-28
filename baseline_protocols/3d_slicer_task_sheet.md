# 3D Slicer Segment Editor Task Sheet

- Input cases: same NIfTI cases listed in the real medical benchmark manifest.
- Target structure: identical target label/structure used for app evaluation.
- Timing start: image and reference task sheet opened, before first segmentation action.
- Timing stop: exported segmentation mask written to disk.
- Allowed tools: Segment Editor manual paint/draw, threshold, grow from seeds, smoothing, logical operators.
- Prompt/seed policy: record every seed, threshold change, and tool switch.
- Correction counting: count every manual edit after the first complete candidate mask.
- Export format: NIfTI labelmap.
- Raw output archive folder: `baseline_outputs/raw/3d_slicer/`.
- Metrics command: `python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir <gt_dir> --pred-dir baseline_outputs/raw/3d_slicer --output results/baseline_eval/3d_slicer`.

No timing or accuracy results are claimed until this sheet is executed.
