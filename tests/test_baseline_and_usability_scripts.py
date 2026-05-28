import subprocess
import sys

import numpy as np
from PIL import Image


def test_baseline_evaluator_not_configured_writes_report(tmp_path):
    out = tmp_path / "baseline"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.baselines.evaluate",
            "--baseline-results",
            "baseline_protocols/baseline_results_template.csv",
            "--gt-dir",
            "NOT_CONFIGURED",
            "--pred-dir",
            "NOT_CONFIGURED",
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert (out / "BASELINE_NOT_RUN.md").exists()


def test_baseline_evaluator_computes_pair_metrics(tmp_path):
    gt = tmp_path / "gt.png"
    pred = tmp_path / "pred.png"
    arr = np.zeros((12, 12), dtype=np.uint8)
    arr[3:8, 4:9] = 255
    Image.fromarray(arr).save(gt)
    Image.fromarray(arr).save(pred)
    csv_path = tmp_path / "baseline.csv"
    csv_path.write_text(
        "baseline_name,dataset_name,case_id,operator_id,input_image_path,ground_truth_mask_path,predicted_mask_path,time_sec,clicks,prompts,corrections,notes\n"
        f"manual,tiny,case1,op1,NOT_CONFIGURED,{gt},{pred},1.2,3,0,1,ok\n",
        encoding="utf-8",
    )
    out = tmp_path / "baseline_eval"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.baselines.evaluate",
            "--baseline-results",
            str(csv_path),
            "--gt-dir",
            "NOT_CONFIGURED",
            "--pred-dir",
            "NOT_CONFIGURED",
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    text = (out / "baseline_metrics.csv").read_text(encoding="utf-8")
    assert "case1" in text
    assert "1.0" in text


def test_usability_analysis_template_writes_not_run(tmp_path):
    out = tmp_path / "usability"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_usability_results.py",
            "--input",
            "forms/usability_results_template.csv",
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert (out / "USABILITY_NOT_RUN.md").exists()
