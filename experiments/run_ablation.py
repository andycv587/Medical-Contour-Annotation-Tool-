import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.workflow import AgenticWorkflow
from app.configs.io import load_structured_config
from benchmarks.datasets import synthetic_smoke_cases
from benchmarks.metrics import binary_metrics
from segmentation.backends import ClassicalBackend, MockBackend


def parse_args():
    parser = argparse.ArgumentParser(description="Run ablation experiments.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--models", default="")
    parser.add_argument("--datasets", default="")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_structured_config(args.config)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    if config.get("mode") != "mock_smoke":
        missing = []
        if args.models and not Path(args.models).exists():
            missing.append(f"models file does not exist: {args.models}")
        if args.datasets and not Path(args.datasets).exists():
            missing.append(f"datasets file does not exist: {args.datasets}")
        if not args.models:
            missing.append("models registry path not provided")
        if not args.datasets:
            missing.append("datasets registry path not provided")
        missing_text = "\n".join(f"- {item}" for item in missing) if missing else "- real ablation execution is intentionally blocked until preflight passes"
        (out / "EXPERIMENT_NOT_RUN.md").write_text(
            "# Experiment Not Run\n\n"
            "This ablation requires configured real datasets/backends. No results were fabricated.\n\n"
            "## Missing Or Blocked\n"
            f"{missing_text}\n",
            encoding="utf-8",
        )
        print(str(out / "EXPERIMENT_NOT_RUN.md"))
        return 2
    rows = []
    conditions = {
        "router_on": {"mock": MockBackend(), "classical": ClassicalBackend()},
        "classical_only": {"classical": ClassicalBackend()},
        "mock_only": {"mock": MockBackend()},
    }
    for cond, backends in conditions.items():
        wf = AgenticWorkflow(backends=backends)
        for case in synthetic_smoke_cases():
            legacy = case.legacy_dict()
            run = wf.segment(legacy["image"], prompt=legacy["prompt"], bbox=legacy["bbox"], metadata=legacy["metadata"])
            metrics = binary_metrics(run.result.mask > 0, legacy["gt"] > 0)
            rows.append({"condition": cond, "case_id": legacy["case_id"], "selected_backend": run.routing.selected_backend, "runtime_sec": run.result.runtime_sec, **metrics})
    fields = sorted({k for row in rows for k in row})
    with open(out / "ablation_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with open(out / "ablation_summary.md", "w", encoding="utf-8") as f:
        f.write("# Ablation Summary\n\n")
        f.write("Mock smoke ablation completed. Synthetic-only results are not publication claims.\n\n")
        f.write("| condition | case_id | selected_backend | dice | runtime_sec |\n|---|---|---|---:|---:|\n")
        for row in rows:
            f.write(f"| {row['condition']} | {row['case_id']} | {row['selected_backend']} | {row.get('dice')} | {row.get('runtime_sec')} |\n")
    print(json.dumps({"status": "ok", "output": str(out), "rows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
