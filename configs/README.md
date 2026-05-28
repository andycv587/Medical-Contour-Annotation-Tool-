# Configuration Templates

Configuration files in this directory are templates. They should not contain private data, real checkpoint paths, or local machine-specific paths unless explicitly intended for local use and excluded from version control.

- `model_registry.example.yaml`: legacy heavy-model checkpoint template used by existing registry tests.
- `models.example.yaml`: default backend status registry used by `python -m app.backends.check`.
- `model_registry.local.template.yaml`: local model registry template with explicit `NOT_CONFIGURED` placeholders.
- `datasets.local.template.yaml`: local public-dataset registry template.
- `experiment_registry.local.template.yaml`: optional local experiment bookkeeping template.

Real model entries must include path, version, source URL, license, and checksum fields before any real backend result is claimed.

Validate templates without running experiments:

```powershell
python -m app.configs.validate --models configs/model_registry.local.template.yaml --datasets configs/datasets.local.template.yaml
```
