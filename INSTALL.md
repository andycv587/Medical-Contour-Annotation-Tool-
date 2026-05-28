# Installation

## Lightweight Mode

```powershell
python -m pip install -e .
```

Run tests:

```powershell
pytest -q
```

Run the lightweight reviewer verification script:

```powershell
python scripts/verify_lightweight_install.py
```

On systems with GNU Make:

```powershell
make test
```

Run synthetic benchmark:

```powershell
python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke
```

Validate unfilled local config templates:

```powershell
python -m app.configs.validate --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml
```

On systems with GNU Make:

```powershell
make benchmark-smoke
```

## GUI

```powershell
python python_app/main.py
```

## Heavy Backends

Heavy model backends require separate installation and checkpoints:

- LangSAM: install `lang-segment-anything` or set `LANGSAM_INFER_CMD`.
- MedSAM: configure `MEDSAM_INFER_CMD` and checkpoint path in backend config.
- MedSAM2: configure `MEDSAM2_INFER_CMD`, checkpoint path, and device.
- Cellpose: install `cellpose`; otherwise the Cellpose backend uses OpenCV fallback for smoke tests.

No heavy model outputs are claimed unless these backends are installed and real benchmarks are run.

Checkpoint metadata should be recorded in a model registry compatible with:

```powershell
configs/models.example.yaml
```

Do not replace `NOT_CONFIGURED` values with real paths unless the checkpoint source, version, license, and SHA256 checksum are known.
