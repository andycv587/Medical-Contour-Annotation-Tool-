import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from app.configs.io import configured, load_structured_config
from benchmarks.datasets import DatasetConfigurationError, load_cases_from_registry
from benchmarks.metrics import binary_metrics
from provenance.logger import ProvenanceLogger
from segmentation.backends import build_default_backends
from segmentation.backends.base import split_command


HEAVY_BACKENDS = {"langsam", "medsam", "medsam2", "cellpose"}
EXTERNAL_ENV = {"langsam": "LANGSAM_INFER_CMD", "medsam": "MEDSAM_INFER_CMD", "medsam2": "MEDSAM2_INFER_CMD", "cellpose": "CELLPOSE_INFER_CMD"}
DEFAULT_CANDIDATES = {
    "medical_3d": ["medsam2", "medsam", "classical", "mock"],
    "microscopy": ["cellpose", "classical", "mock"],
}


def run_preflight(
    *,
    models_path: str,
    datasets_path: str,
    experiment: str,
    output_dir: str = "",
    allow_mock: bool = False,
) -> Dict[str, Any]:
    missing: List[str] = []
    next_actions: List[str] = []
    output = Path(output_dir or f"results/preflight_{experiment}")
    try:
        output.mkdir(parents=True, exist_ok=True)
        probe = output / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except Exception as ex:
        missing.append(f"output_dir not writable: {output} ({ex})")
        next_actions.append("Choose a writable output directory.")

    try:
        model_registry = load_structured_config(models_path)
    except Exception as ex:
        model_registry = {}
        missing.append(f"models config unreadable: {models_path} ({ex})")
        next_actions.append("Create a valid configs/model_registry.local.yaml from the template.")
    try:
        dataset_registry = load_structured_config(datasets_path)
    except Exception as ex:
        dataset_registry = {}
        missing.append(f"datasets config unreadable: {datasets_path} ({ex})")
        next_actions.append("Create a valid configs/datasets.local.yaml from the template.")

    models = _models_by_backend(model_registry)
    enabled = {name for name, model in models.items() if bool(model.get("enabled", False))}
    enabled.add("classical")
    if allow_mock:
        enabled.add("mock")
    else:
        enabled.discard("mock")

    for backend, model in models.items():
        if not bool(model.get("enabled", False)):
            continue
        _configure_external_env(backend, model)
        if backend in HEAVY_BACKENDS:
            _check_heavy_model(backend, model, missing, next_actions)

    all_backends = build_default_backends()
    statuses = {}
    for name in DEFAULT_CANDIDATES.get(experiment, []):
        if name not in enabled or name not in all_backends:
            continue
        try:
            statuses[name] = all_backends[name].check_available().to_dict()
        except Exception as ex:
            statuses[name] = {"available": False, "reason": str(ex)}
    available = [name for name, status in statuses.items() if status.get("available")]
    non_mock_available = [name for name in available if name != "mock"]
    if not available:
        missing.append("no enabled backend is available")
        next_actions.append("Enable classical or configure a real backend in configs/model_registry.local.yaml.")
    if not allow_mock and available and not non_mock_available:
        missing.append("selected backend would be mock but allow_mock is false")
        next_actions.append("Configure a non-mock backend or rerun preflight with --allow-mock for smoke testing only.")

    cases = []
    if dataset_registry:
        try:
            cases = load_cases_from_registry(datasets_path, experiment=experiment, max_cases=1)
        except DatasetConfigurationError as ex:
            missing.extend(ex.missing or [str(ex)])
            next_actions.append(str(ex))
        except Exception as ex:
            missing.append(f"dataset loading failed: {ex}")
            next_actions.append("Check image/mask path patterns and shape compatibility.")
    if cases:
        case = cases[0]
        try:
            _ = binary_metrics(case.gt_mask > 0, case.gt_mask > 0)
        except Exception as ex:
            missing.append(f"metrics failed on tiny loaded pair: {ex}")
            next_actions.append("Verify mask arrays are numeric and shape-compatible.")

    try:
        prov_dir = output / "provenance"
        prov_dir.mkdir(parents=True, exist_ok=True)
        logger = ProvenanceLogger(str(prov_dir / "preflight_session.json"))
        logger.save_session()
    except Exception as ex:
        missing.append(f"provenance output path is not writable: {ex}")
        next_actions.append("Choose a writable provenance output directory.")

    ok = not missing
    result = {
        "ok": ok,
        "experiment": experiment,
        "models_path": models_path,
        "datasets_path": datasets_path,
        "output_dir": str(output),
        "available_backends": available,
        "backend_status": statuses,
        "loaded_case_count_for_probe": len(cases),
        "missing": missing,
        "next_actions": next_actions,
    }
    if not ok:
        _write_failed(result)
    return result


def _check_heavy_model(backend: str, model: Dict[str, Any], missing: List[str], next_actions: List[str]) -> None:
    status = str(model.get("status", ""))
    if status == "NOT_CONFIGURED":
        missing.append(f"models.{backend}.status")
        next_actions.append(f"Fill configs/model_registry.local.yaml for {backend} or disable it.")
    mode = str(model.get("backend_mode", model.get("integration", "")))
    command = str(model.get("command", ""))
    if mode == "external_command":
        if not configured(command):
            missing.append(f"models.{backend}.command")
            next_actions.append(f"Set an executable external command for {backend}.")
        elif not _command_executable(command):
            missing.append(f"models.{backend}.command not executable: {command}")
            next_actions.append(f"Fix the command path for {backend}.")
    checkpoint = str(model.get("checkpoint_path", ""))
    if backend in {"langsam", "medsam", "medsam2"}:
        if not configured(checkpoint):
            missing.append(f"models.{backend}.checkpoint_path")
            next_actions.append(f"Set checkpoint_path for {backend}.")
        elif not Path(checkpoint).exists():
            missing.append(f"models.{backend}.checkpoint_path does not exist: {checkpoint}")
            next_actions.append(f"Download or point to the real {backend} checkpoint.")


def _command_executable(command: str) -> bool:
    parts = split_command(command)
    if not parts:
        return False
    exe = parts[0]
    if Path(exe).exists():
        return True
    return shutil.which(exe) is not None


def _configure_external_env(backend: str, model: Dict[str, Any]) -> None:
    env_name = EXTERNAL_ENV.get(backend)
    command = str(model.get("command", ""))
    if env_name and configured(command):
        os.environ[env_name] = command


def _models_by_backend(model_registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw = model_registry.get("models", {})
    if isinstance(raw, dict):
        return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        return {str(v.get("backend")): dict(v) for v in raw if isinstance(v, dict)}
    return {}


def _write_failed(result: Dict[str, Any]) -> None:
    path = Path("results/PREFLIGHT_FAILED.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Preflight Failed",
        "",
        f"Experiment: `{result.get('experiment')}`",
        "",
        "## Missing Fields Or Checks",
    ]
    lines.extend(f"- {item}" for item in result.get("missing", []))
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in result.get("next_actions", []))
    lines.extend(["", "No benchmark was run and no results were fabricated."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight real benchmark configuration before running experiments.")
    parser.add_argument("--models", required=True)
    parser.add_argument("--datasets", required=True)
    parser.add_argument("--experiment", required=True, choices=["medical_3d", "microscopy"])
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()
    result = run_preflight(
        models_path=args.models,
        datasets_path=args.datasets,
        experiment=args.experiment,
        output_dir=args.output_dir,
        allow_mock=args.allow_mock,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
