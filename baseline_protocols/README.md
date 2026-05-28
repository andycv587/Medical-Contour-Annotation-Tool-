# Baseline Protocols

These files define manual and native-backend baseline collection. They are protocols only until an operator runs them and archives raw outputs.

Required archive folders:

- `baseline_outputs/raw/3d_slicer/`
- `baseline_outputs/raw/itk_snap/`
- `baseline_outputs/raw/qupath/`
- `baseline_outputs/raw/native_backends/`
- `baseline_outputs/evaluated/`

Evaluation command after exports exist:

```powershell
python -m app.baselines.evaluate --baseline-results baseline_protocols/baseline_results_template.csv --gt-dir NOT_CONFIGURED --pred-dir NOT_CONFIGURED --output results/baseline_eval
```

If paths remain `NOT_CONFIGURED`, the evaluator writes `BASELINE_NOT_RUN.md`.

Expected `baseline_results_template.csv` columns:

- `baseline_name`
- `dataset_name`
- `case_id`
- `operator_id`
- `input_image_path`
- `ground_truth_mask_path`
- `predicted_mask_path`
- `time_sec`
- `clicks`
- `prompts`
- `corrections`
- `notes`

The evaluator validates file existence and writes `baseline_metrics.csv` only for rows with real exported masks. It computes binary Dice/IoU/Hausdorff95 and adds object-level precision/recall/F1 when masks contain instance labels.
