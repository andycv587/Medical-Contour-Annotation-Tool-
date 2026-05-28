# Feature Comparison

This table is a paper scaffold. Do not convert `NOT_RUN` or `TO_BE_FILLED` placeholders into results without actual experiments.

| Feature | This software | 3D Slicer | ITK-SNAP | QuPath | Cellpose/native workflows | Status |
|---|---|---|---|---|---|---|
| Tkinter desktop contour annotation | Yes | Comparator protocol | Comparator protocol | Comparator protocol | No | Implemented |
| 2D polygon annotation | Yes | Yes | Yes | Yes | Limited/workflow-specific | Implemented |
| 3D volume mask export | NIfTI | Yes | Yes | Limited | Workflow-specific | Implemented here for NIfTI |
| Microscopy/cell workflow | Yes, with optional Cellpose/fallback | Limited | Limited | Yes | Yes | PARTIAL |
| Transparent backend routing explanation | Yes | No | No | No | No | Implemented |
| Memory-assisted prompt/bbox reuse | Yes, suggestion only | NOT_ASSESSED | NOT_ASSESSED | NOT_ASSESSED | NOT_ASSESSED | Implemented, utility NOT_RUN |
| Provenance sidecars/session logs | Yes | NOT_ASSESSED | NOT_ASSESSED | NOT_ASSESSED | NOT_ASSESSED | Implemented |
| Real benchmark evidence | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | Pending |
