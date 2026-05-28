# Benchmarks

Run the lightweight synthetic smoke benchmark:

```powershell
python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke
```

Outputs:

- `metrics.csv`
- `per_case_results.jsonl`
- `backend_status.json`
- `routing_decisions.jsonl`
- `provenance/`
- `masks/`
- `figures/`
- `report.md`

The synthetic benchmark is for CI and smoke validation only. It must not be reported as real-data performance.

## Real Dataset Templates

- `configs/medical_3d_template.yaml`: MSD subset first; BTCV/FLARE remain optional templates.
- `configs/microscopy_template.yaml`: Cellpose dataset or BBBC first; MoNuSeg/CPM remain optional templates.
- `benchmarks/configs/medical_3d_msd_local.template.yaml`: local MSD-style real benchmark template.
- `benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml`: local microscopy/cell real benchmark template.

Large public datasets are not auto-downloaded by default. Configure local paths explicitly before running real benchmarks.
Real benchmark metrics must remain `NOT_RUN` until public dataset paths and ground-truth masks are configured.

Copy and fill local registries before running:

```powershell
configs/model_registry.local.yaml
configs/datasets.local.yaml
```

Run preflight first:

```powershell
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment medical_3d
python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment microscopy
```

Oracle prompts from ground-truth masks are supported only for controlled benchmark comparability. Reports mark `oracle_prompt=true` and include the required disclosure. Do not describe these results as autonomous segmentation.
