# Final Project Assumptions

Date: 2026-05-03

This file records Andy's current project decisions as implementation assumptions. It is not a claim that real-data experiments or heavy model runs have been completed.

## Confirmed Decisions

- Target Bioinformatics Advances first; upgrade to Bioinformatics Application Note only after strong real benchmark and baseline evidence.
- Article type is Application Note / Software Article.
- Working title: "An agent-routed and memory-augmented annotation workflow for biomedical and bioimage segmentation."
- Main claim: bioimage informatics and reproducible biomedical/bioimage annotation workflow.
- Scientific scope prioritizes microscopy/cell/nuclei segmentation plus 3D biomedical volume annotation.
- Novelty is transparent agentic routing, memory-assisted prompt reuse, and provenance/reproducibility infrastructure.
- The project is not claiming a new segmentation model, SOTA performance, clinical readiness, diagnostic use, or real foundation-model performance without configured backends and benchmark evidence.
- Heavy backends are optional; the lightweight GUI, mock backend, classical methods, tests, and synthetic smoke benchmark must run without GPU/checkpoints.
- LangSAM, MedSAM, and MedSAM2 default to external command bridges.
- Cellpose may be used as an optional Python backend; OpenCV fallback remains available for lightweight tests.
- Real benchmark results remain `NOT_RUN` until public datasets and ground-truth paths are configured.
- Required exports are PNG, NIfTI, polygon JSON, TIFF stack, and COCO JSON where the active annotation state supports it.
- DICOM SEG and RTSTRUCT are future-work clinical interoperability, not implemented claims.

## Still Unknown Fields

- Exact MSD task/subset and labels for the first 3D benchmark.
- Exact Cellpose dataset split or BBBC collection for the first microscopy benchmark.
- Local dataset paths and ground-truth mask paths.
- Heavy backend repository paths, commands, checkpoint paths, checkpoint versions, licenses, and SHA256 checksums.
- GPU, CUDA, and PyTorch environment for heavy experiments.
- Baseline operator, cases, timings, and archived outputs for 3D Slicer, ITK-SNAP, QuPath, and native model workflows.
- Pilot usability participants and assigned tasks.
- Final repository URL, release tag, Zenodo DOI, and any metadata placeholders.

## NOT_CONFIGURED Model Settings

- `langsam`: `enabled=false`, `backend_mode=external_command`, command/checkpoint/source/license/checksum are `NOT_CONFIGURED`.
- `medsam`: `enabled=false`, `backend_mode=external_command`, command/checkpoint/source/license/checksum are `NOT_CONFIGURED`.
- `medsam2`: `enabled=false`, `backend_mode=external_command`, command/checkpoint/source/license/checksum are `NOT_CONFIGURED`.
- `cellpose`: optional direct import; registry remains `NOT_CONFIGURED` unless Andy enables a real Cellpose environment.
- `microsam`: optional placeholder only.
- `mock` and `classical`: configured for lightweight CI/reviewer smoke testing.

## NOT_RUN Experiments

- Real public-dataset benchmark.
- Baseline comparison against Cellpose/native LangSAM/native MedSAM/native MedSAM2.
- Manual/semi-automatic baseline protocols for 3D Slicer, ITK-SNAP, and QuPath.
- Real ablation study on public data.
- Usability/time study with 3-5 users.

## Future-Work Clinical Interoperability

- DICOM SEG and RTSTRUCT are explicitly future work.
- OME-TIFF remains optional unless implemented and tested.
- No clinical deployment, diagnosis, or regulatory-readiness claim should be made.
