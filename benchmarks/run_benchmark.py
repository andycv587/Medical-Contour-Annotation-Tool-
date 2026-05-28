import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.workflow import AgenticWorkflow
from app.configs.io import configured, find_not_configured, load_structured_config
from benchmarks.datasets import (
    BenchmarkCase,
    DatasetConfigurationError,
    bbox_from_mask,
    center_point_from_mask,
    load_cases_from_registry,
    synthetic_smoke_cases,
)
from benchmarks.metrics import binary_metrics, instance_metrics
from benchmarks.report import write_metrics_csv, write_report
from contour_io.exporters import export_tiff_stack
from provenance.logger import ProvenanceLogger
from provenance.schema import build_event_from_result
from segmentation.backends import build_default_backends
from segmentation.backends.base import json_safe, split_command


HEAVY_BACKENDS = {"langsam", "medsam", "medsam2", "cellpose"}
EXTERNAL_ENV = {"langsam": "LANGSAM_INFER_CMD", "medsam": "MEDSAM_INFER_CMD", "medsam2": "MEDSAM2_INFER_CMD", "cellpose": "CELLPOSE_INFER_CMD"}


def parse_args():
    parser = argparse.ArgumentParser(description="Run headless biomedical contour benchmark.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--models", default="")
    parser.add_argument("--datasets", default="")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_structured_config(args.config)
    if args.models:
        config["model_registry_path"] = args.models
    if args.datasets:
        config["dataset_registry_path"] = args.datasets
    output_dir = Path(args.output)
    _prepare_output_dirs(output_dir)

    if config.get("dataset") == "synthetic_smoke":
        return _run_cases(
            config=config,
            output_dir=output_dir,
            cases=synthetic_smoke_cases(),
            dataset_manifest={},
            model_registry={},
            benchmark_kind="synthetic_smoke",
            allow_mock_backend=True,
        )

    try:
        resolved = _resolve_real_benchmark(config)
        return _run_cases(output_dir=output_dir, **resolved)
    except Exception as ex:
        _write_not_run(
            output_dir,
            title="Experiment Not Run",
            reason=str(ex),
            missing=getattr(ex, "missing", None) or find_not_configured(config),
        )
        print(json.dumps({"status": "not_run", "output": str(output_dir), "reason": str(ex)}, indent=2))
        return 2


def _resolve_real_benchmark(config: Dict[str, Any]) -> Dict[str, Any]:
    dataset_registry_path = str(config.get("dataset_registry_path", ""))
    model_registry_path = str(config.get("model_registry_path", ""))
    if not configured(dataset_registry_path):
        raise DatasetConfigurationError("dataset_registry_path is NOT_CONFIGURED", ["dataset_registry_path"])
    if not configured(model_registry_path):
        raise DatasetConfigurationError("model_registry_path is NOT_CONFIGURED", ["model_registry_path"])
    if not Path(dataset_registry_path).exists():
        raise DatasetConfigurationError("dataset_registry_path does not exist; copy and fill configs/datasets.local.template.yaml first", ["dataset_registry_path"])
    if not Path(model_registry_path).exists():
        raise DatasetConfigurationError("model_registry_path does not exist; copy and fill configs/model_registry.local.template.yaml first", ["model_registry_path"])
    experiment = str(config.get("dataset") or config.get("experiment") or "")
    if experiment not in ("medical_3d", "microscopy"):
        raise DatasetConfigurationError("real benchmark config must set dataset to medical_3d or microscopy", ["dataset"])

    model_registry = load_structured_config(model_registry_path)
    dataset_manifest = load_structured_config(dataset_registry_path)
    backend_candidates = [str(x) for x in config.get("backend_candidates", [])]
    allow_mock = bool(config.get("allow_mock_backend", False))
    allow_classical = bool(config.get("allow_classical_baseline", True))
    allow_classical_only = bool(config.get("allow_classical_only", False))
    _validate_model_guardrails(
        model_registry,
        backend_candidates,
        allow_mock=allow_mock,
        allow_classical=allow_classical,
        allow_classical_only=allow_classical_only,
    )

    cases = load_cases_from_registry(
        dataset_registry_path,
        experiment=experiment,
        max_cases=_coerce_optional_int(config.get("max_cases")),
        target_label=_coerce_optional_int(config.get("target_label")),
        channel=_coerce_optional_int(config.get("channel")),
        instance_masks=config.get("instance_masks"),
    )
    return {
        "config": config,
        "cases": cases,
        "dataset_manifest": dataset_manifest,
        "model_registry": model_registry,
        "benchmark_kind": "real_data",
        "allow_mock_backend": allow_mock,
    }


def _run_cases(
    *,
    config: Dict[str, Any],
    output_dir: Path,
    cases: List[BenchmarkCase],
    dataset_manifest: Dict[str, Any],
    model_registry: Dict[str, Any],
    benchmark_kind: str,
    allow_mock_backend: bool,
) -> int:
    _prepare_output_dirs(output_dir)
    stale_not_run = output_dir / "EXPERIMENT_NOT_RUN.md"
    if stale_not_run.exists():
        stale_not_run.unlink()
    (output_dir / "dataset_manifest_resolved.json").write_text(json.dumps(dataset_manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "model_registry_resolved.json").write_text(json.dumps(model_registry, indent=2, sort_keys=True), encoding="utf-8")
    backend_cfg = _backend_config_from_registry(model_registry)
    backends = _filtered_backends(config, model_registry, allow_mock_backend=allow_mock_backend)
    statuses = {name: backend.check_available().to_dict() for name, backend in backends.items()}
    if benchmark_kind == "real_data" and _cellpose_is_fallback(statuses):
        if bool(config.get("allow_classical_only", False)) and "classical" in backends:
            backends.pop("cellpose", None)
            statuses["cellpose"]["available"] = False
            statuses["cellpose"]["reason"] += "; excluded from real benchmark because this is the OpenCV fallback, not real Cellpose"
        else:
            statuses["cellpose"]["available"] = False
            (output_dir / "backend_status.json").write_text(json.dumps(statuses, indent=2, sort_keys=True), encoding="utf-8")
            _write_not_run(
                output_dir,
                title="Experiment Not Run",
                reason="Cellpose was requested but real Cellpose is not installed; OpenCV fallback cannot be reported as Cellpose performance.",
                missing=["install cellpose or set allow_classical_only=true"],
            )
            return 2
    (output_dir / "backend_status.json").write_text(json.dumps(statuses, indent=2, sort_keys=True), encoding="utf-8")
    available = [name for name, status in statuses.items() if status.get("available")]
    if not available:
        _write_not_run(output_dir, title="Experiment Not Run", reason="no requested backend is available", missing=["backend availability"])
        return 2
    if not allow_mock_backend and available == ["mock"]:
        _write_not_run(output_dir, title="Experiment Not Run", reason="only mock backend is available but allow_mock_backend=false", missing=["real backend or classical baseline"])
        return 2

    workflow = AgenticWorkflow(backends=backends)
    session_provenance = output_dir / "provenance" / "session_provenance.json"
    if session_provenance.exists():
        session_provenance.unlink()
    prov_logger = ProvenanceLogger(str(session_provenance))
    rows = []
    oracle_prompt = _uses_oracle_prompt(config)
    warning = (
        "Ground truth was used only to generate standardized prompts for benchmark comparability; "
        "this is not an autonomous segmentation setting."
    )
    with open(output_dir / "per_case_results.jsonl", "w", encoding="utf-8") as case_f, open(output_dir / "routing_decisions.jsonl", "w", encoding="utf-8") as route_f:
        for case in cases:
            prompt, bbox, points, prompt_meta = _prompt_for_case(case, config)
            case_backend_cfg = _case_backend_config(backend_cfg, case, config, prompt_meta)
            run = workflow.segment(
                case.image_array,
                prompt=prompt,
                bbox=bbox,
                points=points,
                metadata=dict(case.metadata, modality=case.modality, benchmark_kind=benchmark_kind),
                config=case_backend_cfg,
            )
            result = run.result
            if oracle_prompt and warning not in result.warnings:
                result.warnings.append(warning)
            mask_path = output_dir / "masks" / f"{case.case_id}_mask.tif"
            mask_for_export = _mask_for_tiff_export(result.mask, case)
            export_tiff_stack(mask_for_export, str(mask_path))
            sidecar = output_dir / "provenance" / f"{case.case_id}.provenance.json"
            event = build_event_from_result(
                result=result,
                image=case.image_array,
                image_filename=case.image_path,
                checkpoint_path=backend_cfg.get(result.backend_name, {}).get("checkpoint_path"),
                prompt=prompt,
                bbox=bbox,
                points=points,
                routing_decision=run.routing.to_dict(),
                parameters={"benchmark_config": config, "prompt_metadata": prompt_meta},
                output_mask_path=str(mask_path),
                export_format="tiff",
            )
            prov_logger.log_event(event, sidecar_path=str(sidecar))
            binary = binary_metrics(result.mask > 0, case.gt_mask > 0)
            inst = instance_metrics(result.mask, case.gt_mask) if case.modality == "microscopy" else {}
            row = {
                "case_id": case.case_id,
                "dataset_name": case.dataset_name,
                "benchmark_kind": benchmark_kind,
                "oracle_prompt": oracle_prompt,
                "prompt_mode": prompt_meta.get("prompt_mode", ""),
                "result_category": _result_category(result.backend_name, benchmark_kind),
                "selected_backend": run.routing.selected_backend,
                "runtime_sec": result.runtime_sec,
                "fallback_rate": 1.0 if run.routing.fallback_history else 0.0,
                "backend_failure_rate": sum(1 for x in run.routing.fallback_history if x.get("status") == "failed"),
                "prompt_count": 1 if prompt or bbox or points else 0,
                "correction_count": None,
                "memory_hit_rate": None,
                **binary,
                **inst,
            }
            rows.append(row)
            case_f.write(json.dumps(json_safe({"case": case.to_dict(), "result": result.to_summary(), "metrics": row}), sort_keys=True) + "\n")
            route_f.write(json.dumps(run.routing.to_dict(), sort_keys=True) + "\n")
            _save_preview(case.image_array, result.mask, output_dir / "figures" / f"{case.case_id}.png")
    write_metrics_csv(str(output_dir / "metrics.csv"), rows)
    write_report(str(output_dir), rows, config, benchmark_kind=benchmark_kind, oracle_prompt=oracle_prompt, warnings=[warning] if oracle_prompt else [])
    print(json.dumps({"status": "ok", "output": str(output_dir), "case_count": len(rows), "benchmark_kind": benchmark_kind}, indent=2))
    return 0


def _validate_model_guardrails(
    model_registry: Dict[str, Any],
    backend_candidates: List[str],
    *,
    allow_mock: bool,
    allow_classical: bool,
    allow_classical_only: bool,
) -> None:
    models = _models_by_backend(model_registry)
    missing: List[str] = []
    classical_available_as_declared = allow_classical and "classical" in backend_candidates
    for backend in backend_candidates:
        if backend == "mock" and not allow_mock:
            missing.append("backend_candidates.mock forbidden because allow_mock_backend=false")
        if backend == "classical" and allow_classical:
            continue
        if backend in HEAVY_BACKENDS:
            model = models.get(backend, {})
            if not model.get("enabled", False) or str(model.get("status", "")) == "NOT_CONFIGURED":
                if allow_classical_only and classical_available_as_declared:
                    continue
                missing.append(f"models.{backend} is requested but NOT_CONFIGURED")
                continue
            mode = str(model.get("backend_mode", model.get("integration", "")))
            command = str(model.get("command", ""))
            if mode == "external_command":
                if not configured(command):
                    missing.append(f"models.{backend}.command")
                elif not _command_executable(command):
                    missing.append(f"models.{backend}.command not executable: {command}")
            checkpoint = str(model.get("checkpoint_path", ""))
            if backend in {"langsam", "medsam", "medsam2"} and not configured(checkpoint):
                missing.append(f"models.{backend}.checkpoint_path")
            elif backend in {"langsam", "medsam", "medsam2"} and not Path(checkpoint).exists():
                missing.append(f"models.{backend}.checkpoint_path does not exist: {checkpoint}")
    if missing:
        raise DatasetConfigurationError("requested heavy backend is NOT_CONFIGURED", missing)


def _models_by_backend(model_registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw = model_registry.get("models", {})
    if isinstance(raw, dict):
        return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        return {str(v.get("backend")): dict(v) for v in raw if isinstance(v, dict)}
    return {}


def _backend_config_from_registry(model_registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    cfg: Dict[str, Dict[str, Any]] = {}
    for backend, model in _models_by_backend(model_registry).items():
        item: Dict[str, Any] = {}
        command = str(model.get("command", ""))
        if configured(command):
            item["cmd"] = command
            env_name = EXTERNAL_ENV.get(backend)
            if env_name:
                os.environ[env_name] = command
        checkpoint = str(model.get("checkpoint_path", ""))
        if configured(checkpoint):
            item["checkpoint_path"] = checkpoint
        for key in (
            "device",
            "model_type",
            "diameter",
            "channels",
            "flow_threshold",
            "cellprob_threshold",
            "timeout_sec",
            "repo_path",
            "cfg",
            "model_cfg",
            "slice_margin",
            "image_size",
        ):
            if key in model:
                item[key] = model[key]
        if item:
            cfg[backend] = item
    return cfg


def _case_backend_config(
    backend_cfg: Dict[str, Dict[str, Any]],
    case: BenchmarkCase,
    config: Dict[str, Any],
    prompt_meta: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    cfg = {name: dict(value) for name, value in backend_cfg.items()}
    if prompt_meta.get("oracle_prompt") and any("bbox_from_ground_truth" in str(x) for x in config.get("prompt_strategy", [])):
        for backend_name in ("medsam", "medsam2"):
            if backend_name in cfg:
                cfg[backend_name]["oracle_gt_mask"] = np.asarray(case.gt_mask)
                cfg[backend_name].setdefault("slice_axis", _infer_slice_axis(case.image_array))
    for backend_name in ("medsam", "medsam2"):
        if backend_name in cfg and "max_medsam_slices" in config:
            cfg[backend_name]["max_slices"] = config.get("max_medsam_slices")
    return cfg


def _filtered_backends(config: Dict[str, Any], model_registry: Dict[str, Any], *, allow_mock_backend: bool):
    candidates = [str(x) for x in config.get("backend_candidates", [])]
    if not candidates:
        candidates = list(build_default_backends())
    if not allow_mock_backend:
        candidates = [name for name in candidates if name != "mock"]
    models = _models_by_backend(model_registry)
    if not models:
        available = build_default_backends()
        return {name: available[name] for name in candidates if name in available}
    enabled = {name for name, model in models.items() if bool(model.get("enabled", False))}
    enabled.update({"classical"})
    if allow_mock_backend:
        enabled.add("mock")
    available = build_default_backends()
    return {name: available[name] for name in candidates if name in available and (name in enabled or name == "classical")}


def _cellpose_is_fallback(statuses: Dict[str, Dict[str, Any]]) -> bool:
    status = statuses.get("cellpose")
    if not status:
        return False
    extra = status.get("extra", {}) or {}
    return status.get("available") and extra.get("mode") == "opencv-fallback"


def _command_executable(command: str) -> bool:
    parts = split_command(command)
    if not parts:
        return False
    exe = parts[0]
    return Path(exe).exists() or shutil.which(exe) is not None


def _prompt_for_case(case: BenchmarkCase, config: Dict[str, Any]):
    strategies = [str(x) for x in config.get("prompt_strategy", [])]
    prompt = case.metadata.get("prompt")
    bbox = case.metadata.get("bbox")
    points = None
    meta: Dict[str, Any] = {"prompt_mode": "case_or_automatic", "oracle_prompt": False}
    if any("bbox_from_ground_truth" in s for s in strategies):
        mask_for_bbox = _representative_mask(case.gt_mask)
        bbox = bbox_from_mask(mask_for_bbox)
        meta.update({"prompt_mode": "oracle_bbox_from_ground_truth", "oracle_prompt": True})
    if any("center_point_from_ground_truth" in s for s in strategies):
        mask_for_point = _representative_mask(case.gt_mask)
        points = center_point_from_mask(mask_for_point)
        meta.update({"oracle_center_point": True, "oracle_prompt": True})
    if case.modality == "microscopy":
        if any("optional_text_prompt" in s for s in strategies):
            prompt = str(config.get("text_prompt", "cells nuclei"))
        elif any("automatic" in s for s in strategies):
            prompt = prompt or "cells nuclei"
    return prompt, bbox, points, meta


def _representative_mask(mask):
    arr = np.asarray(mask)
    if arr.ndim == 3:
        axis = _infer_slice_axis(arr)
        other_axes = tuple(i for i in range(arr.ndim) if i != axis)
        counts = np.count_nonzero(arr > 0, axis=other_axes)
        z = int(np.argmax(counts))
        return np.take(arr, z, axis=axis)
    return arr


def _infer_slice_axis(image) -> int:
    arr = np.asarray(image)
    if arr.ndim != 3:
        return 0
    return int(np.argmin(arr.shape))


def _uses_oracle_prompt(config: Dict[str, Any]) -> bool:
    return any("ground_truth" in str(item) for item in config.get("prompt_strategy", []))


def _result_category(backend_name: str, benchmark_kind: str) -> str:
    if benchmark_kind == "synthetic_smoke":
        return "synthetic smoke"
    if backend_name == "mock":
        return "mock backend result"
    if backend_name == "classical":
        return "classical baseline result"
    return "real backend result"


def _mask_for_tiff_export(mask: np.ndarray, case: BenchmarkCase) -> np.ndarray:
    arr = np.asarray(mask)
    if arr.ndim == 3 and case.modality == "medical_3d":
        return np.moveaxis(arr, _infer_slice_axis(case.image_array), 0)
    return arr


def _prepare_output_dirs(output_dir: Path) -> None:
    for sub in ("masks", "figures", "provenance"):
        (output_dir / sub).mkdir(parents=True, exist_ok=True)


def _write_not_run(output_dir: Path, *, title: str, reason: str, missing: Optional[List[str]] = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    missing = missing or []
    text = [f"# {title}", "", reason, ""]
    if missing:
        text.append("## Missing Fields Or Actions")
        text.extend(f"- {item}" for item in missing)
        text.append("")
    text.append("No benchmark results were generated or fabricated.")
    (output_dir / "EXPERIMENT_NOT_RUN.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def _save_preview(image, mask, path: Path) -> None:
    arr = np.asarray(image)
    if arr.ndim == 3:
        arr2 = _representative_slice(arr)
        mask2 = np.asarray(mask)
        if mask2.ndim == 3:
            mask2 = _representative_slice(mask2)
    else:
        arr2 = arr
        mask2 = np.asarray(mask)
    base = _to_u8(arr2)
    if base.ndim == 3:
        rgb = base[..., :3].copy()
    else:
        rgb = np.stack([base, base, base], axis=-1)
    rgb[mask2 > 0, 0] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb.astype(np.uint8)).save(path)


def _representative_slice(arr: np.ndarray) -> np.ndarray:
    axis = int(np.argmin(arr.shape))
    return np.take(arr, arr.shape[axis] // 2, axis=axis)


def _to_u8(arr):
    arr = arr.astype(np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)
    return np.clip((arr - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)


def _coerce_optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
