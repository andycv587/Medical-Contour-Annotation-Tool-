import json
import subprocess
import sys


def test_synthetic_benchmark_execution(tmp_path):
    out = tmp_path / "synthetic_smoke"
    completed = subprocess.run(
        [
            sys.executable,
            "benchmarks/run_benchmark.py",
            "--config",
            "benchmarks/configs/synthetic_smoke.yaml",
            "--output",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    for name in ["metrics.csv", "per_case_results.jsonl", "backend_status.json", "routing_decisions.jsonl", "report.md"]:
        assert (out / name).exists()
