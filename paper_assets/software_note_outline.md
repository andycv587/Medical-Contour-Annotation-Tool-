# Software Note Outline

## Working Title

An agent-routed and memory-augmented annotation workflow for biomedical and bioimage segmentation

## Abstract Draft

Summary: We present a lightweight desktop and headless workflow for biomedical contour annotation that combines manual polygon editing, classical baselines, optional model backends, transparent routing, geometry memory, provenance logging, and reproducible benchmarking templates.

Availability and Implementation: Source code, documentation, test data, release archive, and DOI are TO_BE_FILLED.

Contact: TO_BE_FILLED.

Supplementary information: TO_BE_FILLED.

## Contributions

- Unified backend API for classical, mock, LangSAM, MedSAM, MedSAM2, and Cellpose-style segmentation.
- Transparent agentic router with structured fallback logs.
- Geometry memory for prompt reuse without storing raw images by default.
- Provenance sidecars and session logs.
- Headless synthetic smoke benchmark and real-dataset templates.
- GUI event logging and export sidecar provenance for reviewer-visible reproducibility.

## Methods Outline

- Image import and annotation model.
- Backend API and command bridge protocol.
- Routing rules and fallback behavior.
- Memory schema and retrieval.
- Provenance and export formats.
- Benchmark metrics.

## Benchmark Outline

- Synthetic smoke tests for CI.
- Public 3D medical datasets after user-provided download.
- Public microscopy datasets after user-provided download.
- Baseline protocols for 3D Slicer, ITK-SNAP, QuPath, Cellpose, micro-SAM, MedSAM/MedSAM2, LangSAM.

## Current Validated Engineering Artifacts

- Lightweight installation and tests.
- Backend status CLI.
- Synthetic benchmark/provenance/routing outputs.
- Config validator and real-experiment preflight.
- Real dataset loader support for paired NIfTI and microscopy image/mask folders.

## Experiments Pending Configuration

- MSD subset or other public medical 3D benchmark.
- Cellpose/BBBC or other public microscopy benchmark.
- Real LangSAM/MedSAM/MedSAM2/Cellpose backend runs.
- Baseline exports from 3D Slicer, ITK-SNAP, QuPath, and native backends.
- Usability/time-study pilot.

## Claim Boundary

Allowed now: software workflow, engineering reproducibility scaffold, synthetic smoke validation, transparent routing/memory/provenance implementation, and guarded real-evidence readiness.

Forbidden now: public-dataset performance, real foundation-model performance, user-study findings, clinical readiness, SOTA segmentation, and autonomous segmentation claims for oracle-prompt benchmarks.

## Rejection Risks Still Unresolved

- No real public-dataset results yet.
- No completed baseline comparison yet.
- No completed usability study yet.
- Heavy backend setup remains external and must be demonstrated before submission.

## Evidence Status After Real-Evidence Readiness

| evidence class | status |
|---|---|
| Engineering evidence | DONE |
| Synthetic smoke validation | DONE |
| Config validation | DONE |
| Preflight safety | DONE |
| Real microscopy benchmark | NOT_RUN |
| Real 3D benchmark | NOT_RUN |
| Real backend performance | NOT_RUN |
| Baseline comparison | NOT_RUN |
| Usability study | NOT_RUN |

## Availability Statement Placeholder

See `docs/availability_statement.md`.

## Limitations

- Synthetic smoke metrics are not real-data claims.
- Heavy model backends require external installation/checkpoints.
- DICOM SEG/RTSTRUCT export is future work.
- User-study results are not available until the protocol is run.

## Reproducibility Checklist

See `docs/reproducibility_checklist.md`.
