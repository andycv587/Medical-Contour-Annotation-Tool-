# Andy Project Decisions

Date recorded: 2026-05-03

These decisions supersede earlier open assumptions unless Andy revises them.

## Publication

- Target journal: Bioinformatics Advances first.
- Upgrade path: Bioinformatics Application Note only if real benchmark and baseline results are strong enough.
- Article type: Application Note / Software Article.
- Working title: "An agent-routed and memory-augmented annotation workflow for biomedical and bioimage segmentation."
- Main claim: bioimage informatics and reproducible biomedical/bioimage annotation workflow.
- Scope priority: microscopy/cell/nuclei segmentation plus 3D biomedical volume annotation.

## Novelty

- Defensible novelty: transparent agentic routing, memory-assisted prompt reuse, and provenance/reproducibility framework.
- The work is not a new segmentation model.
- LangSAM, MedSAM, MedSAM2, Cellpose, and classical methods are backends.
- Do not claim SOTA segmentation performance unless real benchmarks prove it.
- Do not claim clinical readiness, diagnostic use, or real foundation-model performance when only stubs/fallbacks are used.

## Data

- Use public datasets only.
- Medical 3D priority: MSD subset first.
- Optional medical templates: BTCV and FLARE.
- Microscopy/cell priority: Cellpose dataset or BBBC first.
- Optional microscopy templates: MoNuSeg and CPM.
- Large datasets are not committed to the repository.
- Small synthetic data is allowed for CI only.
- Real benchmark results remain `NOT_RUN` until dataset paths and ground-truth masks are configured.

## Backends

- Heavy models are optional dependencies.
- Lightweight app must run without heavy models installed.
- Default LangSAM, MedSAM, and MedSAM2 integration path: external command bridges.
- Direct Python imports are allowed only if stable and tested.
- Cellpose may be an optional Python backend if installable.
- Heavy tests are skipped unless `RUN_HEAVY_TESTS=1`.
- Checkpoints must be configured through a model registry file with path, version, source URL, license, and checksum fields.

## Baselines

Required baselines:

- Classical watershed/levelset/OpenCV.
- Cellpose for microscopy/cell segmentation.
- Native LangSAM workflow for text-prompt 2D segmentation, if configured.
- Native MedSAM/MedSAM2 workflow, if configured.
- 3D Slicer and ITK-SNAP as manual/semi-automatic protocol baselines.
- QuPath as microscopy/pathology protocol baseline.

GUI baselines can remain documented protocols until actually run. Do not fabricate baseline numbers.

## Usability

- Generate templates and an event logger now.
- Do not claim user-study results until actually performed.
- Target 3-5 users for a pilot if possible.
- Log completion time, clicks, prompts, corrections, accepted/rejected preview, selected backend, fallback, export action, and route explanation.

## Memory

- Store prompts, bboxes, points/seeds, backend metadata, runtime, routing explanation, mask summary statistics, and provenance references.
- Do not store raw image pixels/voxels by default.
- Suggest prompts/bboxes; never silently overwrite masks.
- Use project/session-specific memory by default.
- Long-term global memory is optional.
- Add GUI opt-out/toggle behavior where feasible.

## Export/Import

- Required now: PNG mask, NIfTI mask, polygon JSON, TIFF stack, and COCO JSON.
- OME-TIFF is optional future work unless it can be added safely.
- DICOM SEG and RTSTRUCT are future work and should not be implemented now.

## Deployment

- Provide pip install, conda environment, and Docker.
- Target Python 3.10/3.11.
- Support Windows and Linux.
- GPU dependencies are optional.
- CI runs lightweight tests only.
- Use MIT license unless repository ownership requires otherwise.
- Prepare Zenodo-ready metadata, leaving DOI as `TO_BE_FILLED` until release.

## GUI

- Preserve the existing Tkinter GUI.
- Do not migrate to napari, Qt, or web UI now.
- Minimal GUI improvements:
  - backend status panel;
  - routing explanation display;
  - memory suggestion display;
  - session/project save-load;
  - event/provenance logging;
  - export buttons for polygon JSON, TIFF stack, and COCO JSON.

## Paper Assets

- Generate architecture and workflow figure scaffolds.
- Generate benchmark tables with `NOT_RUN` placeholders.
- Generate Bioinformatics-style availability statement.
- Generate reproducibility checklist.
- Do not insert fake numbers.

## Constraints

- Code quality and reproducibility come before broad experiments.
- Never fabricate real-data results.
- Synthetic benchmark is CI/smoke only.
- Stop claims at what the code and experiments actually support.
