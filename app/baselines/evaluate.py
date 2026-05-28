import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.configs.io import configured
from benchmarks.metrics import binary_metrics, instance_metrics
from contour_io.importers import load_image_or_volume


REQUIRED_COLUMNS = [
    "baseline_name",
    "dataset_name",
    "case_id",
    "operator_id",
    "input_image_path",
    "ground_truth_mask_path",
    "predicted_mask_path",
    "time_sec",
    "clicks",
    "prompts",
    "corrections",
    "notes",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate exported baseline masks against ground truth masks.")
    parser.add_argument("--baseline-results", required=True)
    parser.add_argument("--gt-dir", required=True)
    parser.add_argument("--pred-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    baseline_path = Path(args.baseline_results)
    if not baseline_path.exists():
        _write_not_run(out, f"baseline results file does not exist: {baseline_path}")
        return 2
    if not configured(args.gt_dir) or not configured(args.pred_dir):
        rows = _read_rows(baseline_path)
        if not rows or _rows_are_not_configured(rows):
            _write_not_run(out, "gt-dir, pred-dir, or per-row mask paths are NOT_CONFIGURED")
            return 2
        eval_rows, errors = evaluate_rows(rows)
    else:
        gt_dir = Path(args.gt_dir)
        pred_dir = Path(args.pred_dir)
        if not gt_dir.exists() or not pred_dir.exists():
            _write_not_run(out, f"missing directory: gt={gt_dir.exists()} pred={pred_dir.exists()}")
            return 2
        eval_rows, errors = evaluate_dirs(gt_dir, pred_dir), []
    if not eval_rows:
        _write_not_run(out, "no paired prediction/ground-truth masks found")
        return 2
    fields = sorted({k for row in eval_rows for k in row})
    with open(out / "baseline_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(eval_rows)
    if errors:
        (out / "baseline_eval_warnings.md").write_text("# Baseline Evaluation Warnings\n\n" + "\n".join(f"- {e}" for e in errors) + "\n", encoding="utf-8")
    return 0


def evaluate_rows(rows: List[Dict[str, str]]) -> tuple[List[Dict[str, object]], List[str]]:
    out: List[Dict[str, object]] = []
    errors: List[str] = []
    for row in rows:
        status = str(row.get("status", "")).upper()
        if status in {"NOT_RUN", "TO_BE_FILLED"}:
            continue
        gt_path = row.get("ground_truth_mask_path", "")
        pred_path = row.get("predicted_mask_path", "")
        missing = []
        for field, value in [("ground_truth_mask_path", gt_path), ("predicted_mask_path", pred_path)]:
            if not configured(value):
                missing.append(field)
            elif not Path(value).exists():
                missing.append(f"{field} does not exist: {value}")
        if missing:
            errors.append(f"{row.get('case_id', 'unknown')}: " + "; ".join(missing))
            continue
        metrics = evaluate_pair(Path(gt_path), Path(pred_path))
        out.append(
            {
                "baseline_name": row.get("baseline_name", ""),
                "dataset_name": row.get("dataset_name", ""),
                "case_id": row.get("case_id", ""),
                "operator_id": row.get("operator_id", ""),
                "time_sec": row.get("time_sec", ""),
                "clicks": row.get("clicks", ""),
                "prompts": row.get("prompts", ""),
                "corrections": row.get("corrections", ""),
                "ground_truth_mask_path": gt_path,
                "predicted_mask_path": pred_path,
                **metrics,
            }
        )
    return out, errors


def evaluate_dirs(gt_dir: Path, pred_dir: Path) -> List[Dict[str, object]]:
    gt_files = {case_key(path): path for path in _mask_files(gt_dir)}
    pred_files = {case_key(path): path for path in _mask_files(pred_dir)}
    rows: List[Dict[str, object]] = []
    for key in sorted(set(gt_files) & set(pred_files)):
        rows.append({"case_id": key, "ground_truth_mask_path": str(gt_files[key]), "predicted_mask_path": str(pred_files[key]), **evaluate_pair(gt_files[key], pred_files[key])})
    return rows


def evaluate_pair(gt_path: Path, pred_path: Path) -> Dict[str, object]:
    gt, _ = load_image_or_volume(str(gt_path))
    pred, _ = load_image_or_volume(str(pred_path))
    gt = _squeeze_mask(gt)
    pred = _squeeze_mask(pred)
    if gt.shape != pred.shape:
        return {"error": f"shape mismatch gt={gt.shape} pred={pred.shape}"}
    metrics: Dict[str, object] = binary_metrics(pred > 0, gt > 0)
    if _has_instances(gt) or _has_instances(pred):
        metrics.update(instance_metrics(pred, gt))
    return metrics


def _read_rows(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows


def _rows_are_not_configured(rows: List[Dict[str, str]]) -> bool:
    for row in rows:
        gt = row.get("ground_truth_mask_path") or row.get("export_path") or ""
        pred = row.get("predicted_mask_path") or row.get("export_path") or ""
        if configured(gt) and configured(pred):
            return False
    return True


def _mask_files(path: Path):
    exts = {".png", ".tif", ".tiff", ".nii", ".gz"}
    return [p for p in path.iterdir() if p.is_file() and (p.suffix.lower() in exts or p.name.lower().endswith(".nii.gz"))]


def _squeeze_mask(arr) -> np.ndarray:
    out = np.asarray(arr)
    while out.ndim > 2 and 1 in out.shape:
        out = np.squeeze(out)
    return out


def _has_instances(arr) -> bool:
    values = np.unique(np.asarray(arr))
    return values.size > 2 or (values.size > 0 and int(values.max()) > 1)


def case_key(path: Path) -> str:
    name = path.name
    for suffix in (".nii.gz", ".nii", ".tiff", ".tif", ".png", ".jpg", ".jpeg"):
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def _write_not_run(out: Path, reason: str) -> None:
    (out / "BASELINE_NOT_RUN.md").write_text(
        "# Baseline Evaluation Not Run\n\n"
        f"{reason}\n\n"
        "Provide exported baseline masks and matching ground-truth masks before computing metrics. No results were fabricated.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
