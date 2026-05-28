# Usability and Time-Study Protocol

## Participants

- Recommended pilot: 3-5 users.
- Include users familiar with biomedical image annotation; record experience level.

## Tasks

Each participant completes randomized tasks:

1. Manual contouring only.
2. Model-assisted annotation without router.
3. Full agentic router plus memory workflow.

## Metrics

- Task completion time.
- Number of prompts/clicks.
- Number of corrections.
- Dice/IoU against reference.
- Subjective usability rating.
- Failure notes.
- Preview accept/reject counts.
- Backend selected and fallback count.
- Route explanation shown to the user.

## Randomization

Randomize image/task order per participant to reduce learning effects.

## Ethics and Privacy

Use public or de-identified data only. Do not include patient-identifiable data in screenshots, logs, memory files, or provenance.

## Result Table Template

| participant | task | image_id | condition | time_sec | prompts | clicks | corrections | dice | iou | usability_score | failure_notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|

Structured result rows are in `forms/usability_results_template.csv`.

GUI event logs are written as JSONL when the Tkinter app is used. Set `GUI_EVENT_LOG_PATH` to control the log location. Events are observational instrumentation only; they are not a substitute for a completed user study.
