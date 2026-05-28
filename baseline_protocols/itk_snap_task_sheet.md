# ITK-SNAP Task Sheet

- Input cases: same NIfTI cases listed in the real medical benchmark manifest.
- Target structure: identical target label/structure used for app evaluation.
- Timing start: image opened and task target visible.
- Timing stop: segmentation saved.
- Allowed tools: manual contouring, active contour, region competition, threshold preprocessing.
- Prompt/seed policy: record seed placement, active-contour parameters, and restarts.
- Correction counting: count seed edits, parameter restarts, and manual contour corrections.
- Export format: NIfTI segmentation image.
- Raw output archive folder: `baseline_outputs/raw/itk_snap/`.
- Metrics command: `python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir <gt_dir> --pred-dir baseline_outputs/raw/itk_snap --output results/baseline_eval/itk_snap`.

No timing or accuracy results are claimed until this sheet is executed.
