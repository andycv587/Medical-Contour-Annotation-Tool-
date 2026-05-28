# Model Backends

The lightweight package must run without heavy model dependencies. Heavy backends are enabled only through local configuration.

## Registry Files

- Example defaults: `configs/models.example.yaml`
- Local template: `configs/models.local.template.yaml`
- Optional runtime override: set `MODEL_REGISTRY_PATH`

Heavy models default to `enabled=false` and `NOT_CONFIGURED` paths. Required registry fields include backend mode, command, repo path, checkpoint path, checksum, source URL, license, device, Python executable, and extra args.

## Current Lightweight Status

- `mock`: configured and always available for CI/smoke tests.
- `classical`: configured through OpenCV.
- `cellpose`: optional; reports OpenCV fallback if Cellpose is not installed.
- `langsam`, `medsam`, `medsam2`: `NOT_CONFIGURED` unless external command bridges or tested direct imports are provided.
- `microsam`: optional placeholder only.

Run:

```powershell
python -m app.backends.check
```

The checker should report `NOT_CONFIGURED` for missing heavy models rather than crashing.
