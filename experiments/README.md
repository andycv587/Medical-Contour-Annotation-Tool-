# Ablation Experiments

Run the CI-safe mock smoke ablation:

```powershell
python experiments/run_ablation.py --config experiments/ablation_configs/mock_smoke.yaml --output results/mock_ablation
```

Real ablations are provided as templates and should be run only after datasets and real backends are configured:

1. Router off vs router on.
2. No memory vs short-term memory vs long-term memory.
3. Manual seed/bbox only vs LangSAM seed plus MedSAM/MedSAM2.
4. Classical CellSeg/watershed vs Cellpose vs full agentic workflow.

If prerequisites are missing, the runner writes `EXPERIMENT_NOT_RUN.md` instead of fabricating conclusions.

## Local Real-Data Templates

- `experiments/ablation_configs/medical_3d_router_memory_local.template.yaml`
- `experiments/ablation_configs/microscopy_backend_memory_local.template.yaml`

These configs are intentionally `NOT_CONFIGURED`. Copy them to local files after datasets and model registries are filled. If data/checkpoints are still missing, do not create `ablation_metrics.csv`; write `EXPERIMENT_NOT_RUN.md` instead.
