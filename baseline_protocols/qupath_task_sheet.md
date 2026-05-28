# QuPath Task Sheet

- Input cases: same microscopy/pathology cases listed in the real microscopy benchmark manifest.
- Target structure: cells, nuclei, or tissue compartment defined by the benchmark.
- Timing start: image opened in project.
- Timing stop: object detections or mask export completed.
- Allowed tools: cell detection, thresholding, pixel classifier, object classifier, manual object correction.
- Prompt/seed policy: record detection parameters and classifier training interactions.
- Correction counting: count manual object edits, classifier retraining rounds, and rejected detection runs.
- Export format: GeoJSON, labeled mask TIFF/PNG, or measurements plus reconstructed mask.
- Raw output archive folder: `baseline_outputs/raw/qupath/`.
- Metrics command: `python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir <gt_dir> --pred-dir baseline_outputs/raw/qupath --output results/baseline_eval/qupath`.

No timing or accuracy results are claimed until this sheet is executed.
