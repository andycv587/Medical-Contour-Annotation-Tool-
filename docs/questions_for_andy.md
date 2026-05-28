# Andy Decisions and Remaining Questions

Date updated: 2026-05-03

Andy has answered the first decision round. The current source of truth is also recorded in `docs/project_decisions.md`.

## Answered Decisions

| Area | Current decision |
|---|---|
| Publication target | Bioinformatics Advances first; upgrade to Bioinformatics Application Note only if real benchmarks and baselines are strong enough. |
| Article type | Application Note / Software Article. |
| Working title | "An agent-routed and memory-augmented annotation workflow for biomedical and bioimage segmentation." |
| Main claim | Bioimage informatics and reproducible biomedical/bioimage annotation workflow. |
| Scope | Prioritize microscopy/cell/nuclei segmentation plus 3D biomedical volume annotation. |
| Novelty | Transparent agentic routing, memory-assisted prompt reuse, and provenance/reproducibility framework. |
| Model claim boundary | Not a new segmentation model; no SOTA, clinical-readiness, diagnostic, or real-model-performance claims without evidence. |
| Datasets | Public datasets only; MSD subset first for 3D, Cellpose dataset or BBBC first for microscopy/cells. |
| Large data policy | Do not commit large datasets; provide manifests and download/configuration instructions. |
| Synthetic data policy | CI/smoke only; no real-performance claims. |
| Backend integration | Heavy models optional; lightweight app must run without them; external command bridges are default for LangSAM, MedSAM, MedSAM2. |
| Heavy tests | Skip unless `RUN_HEAVY_TESTS=1`. |
| Checkpoints | Use model registry with path, version, source URL, license, checksum. |
| Baselines | Classical OpenCV, Cellpose, native LangSAM if configured, native MedSAM/MedSAM2 if configured, 3D Slicer, ITK-SNAP, QuPath. |
| Usability | Generate templates/event logger now; no study results until performed; target 3-5 users if possible. |
| Memory | Store prompts/bboxes/points/seeds/backend/routing/runtime/mask summary/provenance references; no raw pixels by default. |
| Required exports | PNG mask, NIfTI mask, polygon JSON, TIFF stack, COCO JSON. |
| Future exports | OME-TIFF optional; DICOM SEG/RTSTRUCT future work only. |
| Deployment | pip, conda, Docker; Python 3.10/3.11; Windows and Linux; optional GPU dependencies; MIT license unless ownership requires otherwise. |
| GUI | Preserve Tkinter; add backend status, route explanation, memory suggestions, project save-load, provenance/event logging, and extra export buttons. |
| Paper assets | Architecture/workflow figure scaffolds, `NOT_RUN` benchmark tables, availability statement, reproducibility checklist. |
| Hard constraint | Code quality and reproducibility before broad experiments; never fabricate results. |

## Remaining Questions Before Real Experiments

### Dataset Configuration

- Which MSD task/subset should be used first?
- Which Cellpose dataset split or which BBBC collection should be used first?
- What local paths should be used for each dataset?
- Which target labels/classes should be benchmarked?
- What train/validation/test split should be reported?

### Real Backend Configuration

- Where are the local LangSAM, MedSAM, MedSAM2, and optional Cellpose environments?
- What exact external bridge commands should be used?
- What checkpoint paths, versions, source URLs, licenses, and SHA256 checksums should be entered into the model registry?
- What GPU/CUDA/PyTorch environment should be recorded for heavy runs?

### Baseline Execution

- Who will run 3D Slicer, ITK-SNAP, and QuPath protocol baselines?
- Which cases should be used for manual/semi-automatic baseline timing?
- Where should raw baseline outputs be archived?

### Usability Study

- Can 3-5 pilot users be recruited?
- Are users domain experts, students, or general technical users?
- Which exact tasks/images should be assigned?
- Should user-study logs be anonymized by participant ID only?

### Release Metadata

- What GitHub URL should be used in `CITATION.cff` and the availability statement?
- What copyright holder should replace `TO_BE_FILLED` in `LICENSE`?
- What release tag should be archived?
- Should Zenodo metadata be prepared now with DOI left as `TO_BE_FILLED`?
