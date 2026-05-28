# Reject-Risk Audit

Date: 2026-05-03

## Strict Reviewer Risks

| Issue | Why reviewer may reject | What was fixed | Remaining status | Blocker | Exact next action |
|---|---|---|---|---|---|
| No real public-dataset benchmark | Application Note reviewers expect evidence on biomedical data. | Dataset manifests, guarded loaders, and benchmark templates exist. | Unresolved | Andy/user info | Configure MSD and Cellpose/BBBC paths, then run benchmark. |
| No baseline comparison | Without baselines, usefulness is not demonstrated. | Classical backend, mock ablation, and baseline protocols exist. | Unresolved | User info + external dependencies | Run classical, Cellpose/native model, and manual GUI baselines. |
| Wrapper/glue-code concern | Combining existing models may be seen as insufficient novelty. | Canonical router, GUI route explanation, memory schema, provenance, and verification scripts are now clearer. | Partially unresolved | Missing evidence | Run ablations showing router/memory/provenance value. |
| Heavy backend claims unsupported | LangSAM/MedSAM/MedSAM2 are not configured here. | Model registry and checker report `NOT_CONFIGURED`; docs forbid overclaiming. | Unresolved | External dependency | Add real commands/checkpoints/licenses/checksums before claiming. |
| Usability improvement unproven | Event logging alone is not user evidence. | GUI event logger and study templates exist. | Unresolved | User info | Recruit 3-5 users and run timed tasks. |
| Clinical interoperability absent | Medical image reviewers may expect DICOM SEG/RTSTRUCT. | Docs mark DICOM SEG/RTSTRUCT as future work. | Unresolved but acceptable if scoped | Missing implementation | Keep clinical formats out of claims unless implemented/tested. |
| Release metadata incomplete | Reviewers need installable, archived software. | Verification script and docs improved. | Unresolved | User info | Fill copyright, authors, repo URL, release tag, Zenodo metadata. |

## Current Safe Claim Boundary

Safe: lightweight desktop annotation workflow, transparent routing/fallback logging, optional backend registry, memory/provenance schemas, GUI event/export provenance, synthetic smoke validation, and real-experiment templates that refuse to fabricate results.

Unsafe until run: real segmentation accuracy, runtime superiority, baseline superiority, user efficiency, foundation-model performance, and clinical utility.

## Evidence Status After Real-Evidence Readiness

| evidence class | status | reviewer implication |
|---|---|---|
| Engineering evidence | DONE | Supports software-availability and reproducibility claims. |
| Synthetic smoke validation | DONE | Supports execution smoke tests only. |
| Config validation | DONE | Shows local real-run configs can be checked without running experiments. |
| Preflight safety | DONE | Shows missing data/checkpoints fail safely. |
| Real microscopy benchmark | NOT_RUN | Remains a rejection risk. |
| Real 3D benchmark | NOT_RUN | Remains a rejection risk. |
| Real backend performance | NOT_RUN | Do not claim LangSAM/MedSAM/MedSAM2/Cellpose performance. |
| Baseline comparison | NOT_RUN | Do not claim superiority over Slicer/ITK-SNAP/QuPath/native tools. |
| Usability study | NOT_RUN | Do not claim time savings or usability outcomes. |
