# Native Backend Task Sheet

- Input cases: same cases used by app benchmark.
- Target structure: identical benchmark target.
- Timing start: native command launched or notebook cell started after data is loaded.
- Timing stop: exported mask written.
- Allowed tools: upstream LangSAM, MedSAM, MedSAM2, Cellpose, Cellpose-SAM, or micro-SAM workflows.
- Prompt/seed policy: use the same text, bbox, point, or oracle benchmark prompts declared in the app benchmark.
- Correction counting: count manual edits or reruns after first candidate mask.
- Export format: NIfTI for 3D masks; TIFF/PNG for 2D or instance masks.
- Raw output archive folder: `baseline_outputs/raw/native_backends/`.
- Metrics command: `python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir <gt_dir> --pred-dir baseline_outputs/raw/native_backends --output results/baseline_eval/native_backends`.

Record command line, checkpoint path/hash, source URL, license, device, and runtime for every native backend result.
