# Environment

## Supported Lightweight Environment

- Python: 3.10+
- OS: Windows, Linux, macOS expected for headless tools; GUI tested primarily on Windows/Tkinter.
- Required Python packages: see `requirements.txt`.

## Modes

- Lightweight mode: mock/classical/OpenCV fallback, bridge stubs, synthetic smoke tests.
- Mock backend mode: CI-safe deterministic masks.
- Full model mode: external LangSAM/MedSAM/MedSAM2 commands and optional Cellpose.

## Environment Variables

- `LANGSAM_INFER_CMD`: command implementing the LangSAM 2D bridge.
- `MEDSAM_INFER_CMD`: command implementing the MedSAM 2D bridge.
- `MEDSAM2_INFER_CMD`: command implementing the MedSAM2 3D bridge.
- `AGENT_ROUTER_CMD`: optional external VLM/LLM router command.
- `MODEL_REGISTRY_PATH`: optional local model registry path, usually `configs/models.local.yaml`.
- `RUN_HEAVY_TESTS=1`: enable heavy pytest tests if present.

## Model Registry

Optional heavy checkpoints must be described in `configs/models.example.yaml`-compatible files. Each real model entry needs:

- checkpoint path;
- checkpoint version;
- source URL;
- license;
- SHA256 checksum.

The example registry is intentionally `NOT_CONFIGURED` and must not be used as evidence of real backend availability.

Dataset manifests default to `NOT_CONFIGURED` paths. Real benchmarks must not run until public dataset image and mask directories are configured.

## Known Limitations

- DICOM SEG/RTSTRUCT export is not implemented.
- Synthetic smoke metrics are not real-data claims.
- Heavy model direct imports may require CUDA-specific dependency resolution.
