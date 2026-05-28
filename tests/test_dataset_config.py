import subprocess
import sys

from benchmarks.datasets import load_dataset_manifest, validate_dataset_manifest


def test_dataset_manifest_template_is_not_configured():
    manifest = load_dataset_manifest("configs/datasets.example.yaml")
    assert manifest["medical_3d"]
    assert manifest["microscopy"]
    summary = validate_dataset_manifest("configs/datasets.example.yaml")
    assert summary["dataset_count"] >= 2
    assert summary["configured_count"] == 0


def test_real_template_refuses_to_run_without_configured_paths(tmp_path):
    out = tmp_path / "medical_template"
    completed = subprocess.run(
        [
            sys.executable,
            "benchmarks/run_benchmark.py",
            "--config",
            "benchmarks/configs/medical_3d_template.yaml",
            "--output",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert (out / "EXPERIMENT_NOT_RUN.md").exists()
