# Reproducibility Checklist

- [ ] Source code public at stable GitHub URL.
- [ ] Open-source license included.
- [ ] Release tag created.
- [ ] Zenodo/Figshare/Software Heritage archive created.
- [ ] Test data publicly available.
- [ ] `pip install -e .` works in a clean environment.
- [ ] `pytest -q` passes without heavy model checkpoints.
- [ ] Synthetic smoke benchmark runs.
- [ ] Real benchmark dataset paths documented.
- [ ] Heavy backend checkpoint paths documented.
- [ ] `python -m app.configs.validate --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml` passes.
- [ ] `python -m app.experiments.preflight ... --experiment medical_3d` passes before real medical benchmark.
- [ ] `python -m app.experiments.preflight ... --experiment microscopy` passes before real microscopy benchmark.
- [ ] Provenance sidecars generated for segmentation outputs.
- [ ] No patient-identifiable data in logs, examples, screenshots, memory, or provenance.
- [ ] Application Note availability statement filled.
