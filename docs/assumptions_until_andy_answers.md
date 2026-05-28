# Assumptions Until Andy Answers

These assumptions are safe defaults for continued engineering. They are not scientific claims and should be revised when Andy provides reference information.

Most high-level decisions were answered on 2026-05-03 and are now recorded in `docs/project_decisions.md`. This file now only preserves conservative defaults for details that remain unresolved.

## Publication and Scope

- Confirmed publication target: Bioinformatics Advances first, with possible Bioinformatics Application Note upgrade only after strong real benchmark/baseline evidence.
- Confirmed scientific scope: bioimage informatics and reproducible biomedical/bioimage annotation workflows.
- Confirmed emphasis: transparent routing, memory-assisted prompt reuse, provenance, and reproducibility.
- Avoid claiming state-of-the-art segmentation performance until real benchmarks are run.
- Avoid claiming clinical readiness, diagnostic use, or regulatory suitability.
- Avoid claiming real LangSAM/MedSAM/MedSAM2/Cellpose performance when only stubs or fallbacks are used.

## Novelty

- Treat the strongest provisional contribution as transparent agentic routing plus memory/provenance for reproducible annotation workflows.
- Treat LangSAM, MedSAM, MedSAM2, Cellpose, and classical methods as optional backends, not as novel algorithms.
- Treat memory-assisted prompt reuse as a feature requiring validation, not as a proven performance improvement.
- Treat 3D medical plus microscopy support as broad workflow coverage, not as evidence of superior generalization.

## Data and Benchmarks

- Real benchmarks require real public or user-provided datasets with ground-truth masks.
- Do not invent dataset results.
- Use `NOT_RUN` placeholders in tables until scripts have actually run.
- Large datasets should be referenced through download instructions and manifests, not committed to the repository.
- Small sample data may be added only if license/privacy are confirmed.
- Synthetic data can be used for CI and smoke testing only.
- Synthetic Dice values are engineering checks and should not be framed as biological or clinical benchmark performance.

## Model Backends

- Heavy model dependencies should be optional.
- The lightweight app should run without heavy models installed.
- Mock/stub backends should remain available for CI and reviewer smoke tests.
- Real backends should be enabled through explicit configuration and availability checks.
- External command bridges are the safest default for heavy models until direct import adapters are tested.
- Checkpoint paths should default to `NOT_CONFIGURED`.
- Any checkpoint used in experiments needs source URL, license, version, path, and checksum.

## Baselines

- Baseline comparison templates can be created now, but results remain `NOT_RUN`.
- Baselines should include at least classical segmentation and native model workflows where feasible.
- Manual GUI tools such as 3D Slicer, ITK-SNAP, and QuPath should be documented as protocols unless actual experiments are performed.
- Manual annotation time studies require named participants/tasks before any result is claimed.

## Usability/Time Study

- Generate templates now, but do not claim a user study has been performed.
- Default logged metrics: completion time, click count, prompt count, correction count, backend selected, route explanation, accepted/rejected previews, and export action.
- Logs should avoid raw image data by default.

## Memory

- Memory should store geometry, prompts, backend metadata, timings, and provenance references only.
- Memory should not store raw image pixels/voxels by default.
- Memory suggestions should be image/project-specific by default.
- Global memory should remain optional and clearly documented.
- Memory reuse should suggest bboxes/prompts, not silently overwrite masks.
- Persisted memory should be opt-out or clearly toggleable in the GUI.

## Export/Import

- Preserve current PNG and NIfTI export.
- Add polygon JSON before heavier interoperability formats.
- Add COCO JSON only if microscopy/cell workflows are prioritized.
- Add TIFF stack for microscopy masks if needed.
- Treat OME-TIFF as optional until dependency and metadata requirements are confirmed.
- Treat DICOM SEG and RTSTRUCT as future work unless Andy explicitly prioritizes clinical interoperability.

## Deployment

- Target Python 3.10 or 3.11 unless Andy specifies otherwise.
- Prioritize Windows compatibility because the current helper is Windows-specific, while keeping code cross-platform where practical.
- Keep the existing package install path lightweight-first.
- Treat the current MIT license and citation metadata as placeholders until Andy confirms copyright holder, authors, repository URL, and release plan.
- Keep optional heavy extras/configuration separate from the lightweight install.
- CI should run lightweight tests only by default.
- Heavy model tests should be skipped unless `RUN_HEAVY_TESTS=1` and required configs are present.

## GUI and Workflow

- Preserve the current Tkinter GUI by default.
- Do not migrate to napari, Qt, or a web UI unless Andy explicitly chooses that direction.
- Minimal acceptable GUI improvements: backend status indicators, routing explanation display, memory suggestion visibility, and project/session save-load.
- Keep stubs visible as demo/CI backends, but clearly label them as stubs.

## Paper Artifacts

- Architecture diagrams and benchmark tables can be generated with placeholders.
- Availability statement should only claim what exists: source repository, lightweight install path, smoke test, optional backend bridges, and future DOI once archived.
- Reproducibility checklist should distinguish DONE, PARTIAL, MISSING, and BLOCKED items.

## Hard Constraints

- If time is limited, prioritize reproducible engineering artifacts before broad experiments.
- Do not add claims faster than tests, configs, and evidence can support.
- Prefer small, reviewable implementation steps over major rewrites.
