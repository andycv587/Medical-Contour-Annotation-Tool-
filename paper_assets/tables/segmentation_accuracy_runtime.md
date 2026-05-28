# Segmentation Accuracy And Runtime

| dataset | case_count | backend | prompt_setting | dice | iou | hausdorff95 | object_f1 | runtime_sec | status |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| synthetic_smoke | 2 | classical/fallback | synthetic smoke | smoke_only | smoke_only | smoke_only | smoke_only | smoke_only | smoke_only |
| medical_3d | NOT_RUN | MedSAM2 | oracle/user prompt | NOT_RUN | NOT_RUN | NOT_RUN | NA | NOT_RUN | NOT_CONFIGURED |
| medical_3d | NOT_RUN | MedSAM | oracle/user prompt | NOT_RUN | NOT_RUN | NOT_RUN | NA | NOT_RUN | NOT_CONFIGURED |
| medical_3d | NOT_RUN | classical | automatic/bbox-assisted | NOT_RUN | NOT_RUN | NOT_RUN | NA | NOT_RUN | NOT_CONFIGURED |
| microscopy | NOT_RUN | Cellpose | automatic/text prompt | NOT_RUN | NOT_RUN | NA | NOT_RUN | NOT_RUN | NOT_CONFIGURED |
| microscopy | NOT_RUN | classical | automatic | NOT_RUN | NOT_RUN | NA | NOT_RUN | NOT_RUN | NOT_CONFIGURED |

Real-data rows must remain `NOT_RUN` until dataset paths, ground-truth masks, and backend configurations are available.
