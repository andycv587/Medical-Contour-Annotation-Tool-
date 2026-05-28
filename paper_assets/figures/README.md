# Figure Templates

- Figure 1: system architecture.
- Figure 2: agentic routing workflow.
- Figure 3: example segmentation outputs.
- Figure 4: memory reuse effect.
- Figure 5: benchmark runtime/accuracy plot.

Actual figures should be generated from benchmark outputs. Do not manually invent quantitative plots.

Use `NOT_RUN` callouts for panels that require real-data metrics. Synthetic panels may be labeled only as smoke-test examples.

Required claim boundary:

- Figure 1 and Figure 2 may describe implemented software architecture/workflow.
- Figure 3 may show synthetic smoke outputs until real public data is configured.
- Figure 4 memory reuse effect remains `NOT_RUN`.
- Figure 5 runtime/accuracy plot remains `NOT_RUN` for real data.
- Figure captions must state when panels are synthetic smoke examples.
- Do not plot real-data accuracy/runtime until benchmark outputs exist.

Current scaffolds:

- `architecture_scaffold.md`
- `workflow_scaffold.md`
