import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    commands = [
        ("import checks", [sys.executable, "-c", "import agent.workflow, app.backends.check, benchmarks.run_benchmark, contour_io.exporters, memory.schema, provenance.logger; print('imports ok')"]),
        ("backend checker", [sys.executable, "-m", "app.backends.check"]),
        ("lightweight pytest", [sys.executable, "-m", "pytest", "-q"]),
        (
            "synthetic benchmark",
            [
                sys.executable,
                "benchmarks/run_benchmark.py",
                "--config",
                "benchmarks/configs/synthetic_smoke.yaml",
                "--output",
                "results/verify_synthetic_smoke",
            ],
        ),
        (
            "mock ablation",
            [
                sys.executable,
                "experiments/run_ablation.py",
                "--config",
                "experiments/ablation_configs/mock_smoke.yaml",
                "--output",
                "results/verify_mock_ablation",
            ],
        ),
        (
            "provenance inspect",
            [
                sys.executable,
                "-m",
                "app.provenance.inspect",
                "results/verify_synthetic_smoke/provenance/session_provenance.json",
            ],
        ),
        (
            "compileall",
            [
                sys.executable,
                "-m",
                "compileall",
                "python_app",
                "agent",
                "segmentation",
                "app",
                "benchmarks",
                "provenance",
                "tests",
                "contour_io",
                "memory",
            ],
        ),
    ]
    results = []
    for label, cmd in commands:
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        results.append({"step": label, "returncode": completed.returncode})
        print(f"\n[{label}] {'PASS' if completed.returncode == 0 else 'FAIL'}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
    ok = all(item["returncode"] == 0 for item in results)
    print("\nSummary")
    print(json.dumps({"status": "PASS" if ok else "FAIL", "steps": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
