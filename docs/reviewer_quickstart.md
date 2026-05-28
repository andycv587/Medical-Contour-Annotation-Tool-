# Reviewer Quickstart

```powershell
python -m pip install -e .
python -m app.backends.check
python -m app.configs.validate --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml
pytest -q
python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke
python -m app.provenance.inspect results/synthetic_smoke/provenance/session_provenance.json
python -m app.experiments.preflight --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml --experiment medical_3d
python scripts/verify_lightweight_install.py
```

Expected lightweight behavior:

- Mock and classical backends are available.
- Cellpose backend is available through real Cellpose if installed, otherwise OpenCV fallback.
- LangSAM/MedSAM/MedSAM2 are unavailable unless environment command bridges are configured.
- Synthetic smoke benchmark writes metrics, masks, routing decisions, provenance, figures, and report.
- Config validation passes schema checks and reports `NOT_CONFIGURED` placeholders.
- Preflight on templates fails safely and writes `results/PREFLIGHT_FAILED.md`.

Synthetic benchmark results are smoke tests only and should not be interpreted as real-data performance.

For a shorter smoke-only reviewer path:

```powershell
python scripts/verify_reviewer_quickstart.py
```
