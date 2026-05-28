# Ablation Study

| dataset | condition | backend_candidates | memory_mode | dice | iou | runtime_sec | correction_count | status |
|---|---|---|---|---:|---:|---:|---:|---|
| synthetic_smoke | mock smoke | mock/classical | no_memory | smoke_only | smoke_only | smoke_only | NA | smoke_only |
| medical_3d | router off vs on | MedSAM2/MedSAM/classical | no/session/long_term | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_CONFIGURED |
| microscopy | Cellpose vs classical | Cellpose/classical | no/session | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_CONFIGURED |

Synthetic smoke ablation is an engineering check only. Router or memory benefit claims require real tasks and should remain `NOT_RUN`.
