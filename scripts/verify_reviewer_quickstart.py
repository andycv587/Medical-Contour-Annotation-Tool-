import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(label, cmd):
    completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(f"[{label}] {'PASS' if completed.returncode == 0 else 'FAIL'}")
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip())
    return completed.returncode == 0


def main() -> int:
    steps = [
        ("backend checker", [sys.executable, "-m", "app.backends.check"]),
        (
            "synthetic benchmark",
            [
                sys.executable,
                "benchmarks/run_benchmark.py",
                "--config",
                "benchmarks/configs/synthetic_smoke.yaml",
                "--output",
                "results/reviewer_synthetic_smoke",
            ],
        ),
        (
            "provenance inspect",
            [
                sys.executable,
                "-m",
                "app.provenance.inspect",
                "results/reviewer_synthetic_smoke/provenance/session_provenance.json",
            ],
        ),
    ]
    ok = all(run(label, cmd) for label, cmd in steps)
    print(f"Reviewer quickstart {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
