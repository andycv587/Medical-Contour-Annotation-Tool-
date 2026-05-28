import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.configs.io import configured, load_structured_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local model/dataset/experiment registries from an answer file.")
    parser.add_argument("--answers", default="configs/andy_real_run_answers.template.yaml")
    parser.add_argument("--output-dir", default="configs")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    paths = generate_local_configs(args.answers, args.output_dir, force=args.force)
    print(json.dumps({"status": "ok", "written": paths, "next_commands": next_commands()}, indent=2))
    return 0


def generate_local_configs(answers_path: str, output_dir: str, *, force: bool = False) -> Dict[str, str]:
    answers = load_structured_config(answers_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    payloads = {
        "model_registry.local.yaml": build_model_registry(answers),
        "datasets.local.yaml": build_dataset_registry(answers),
        "experiment_registry.local.yaml": build_experiment_registry(answers),
    }
    written: Dict[str, str] = {}
    for name, payload in payloads.items():
        path = out / name
        if path.exists() and not force:
            raise FileExistsError(f"{path} already exists; pass --force to overwrite")
        path.write_text(dump_yaml(payload), encoding="utf-8")
        written[name] = str(path)
    return written


def build_model_registry(answers: Dict[str, Any]) -> Dict[str, Any]:
    models = answers.get("models", {})
    cellpose = dict(models.get("cellpose", {}))
    medsam = dict(models.get("medsam", {}))
    medsam2 = dict(models.get("medsam2", {}))
    langsam = dict(models.get("langsam", {}))
    return {
        "version": 1,
        "models": {
            "mock": {
                "enabled": True,
                "backend_mode": "internal",
                "status": "CONFIGURED",
            },
            "classical": {
                "enabled": True,
                "backend_mode": "internal",
                "status": "CONFIGURED",
            },
            "cellpose": {
                "enabled": bool(cellpose.get("enabled", False)),
                "backend_mode": cellpose.get("backend_mode", "direct_import"),
                "command": cellpose.get("command", "NOT_CONFIGURED"),
                "model_type": cellpose.get("model_type", "cyto"),
                "diameter": cellpose.get("diameter"),
                "channels": cellpose.get("channels", [0, 0]),
                "device": cellpose.get("device", "cpu"),
                "source_url": cellpose.get("source_url", "https://github.com/MouseLand/cellpose"),
                "license": cellpose.get("license", "TO_BE_FILLED"),
                "status": "CONFIGURED" if bool(cellpose.get("enabled", False)) else "NOT_CONFIGURED",
            },
            "medsam": _external_model("medsam", medsam),
            "medsam2": _external_model("medsam2", medsam2),
            "langsam": _external_model("langsam", langsam),
        },
    }


def build_dataset_registry(answers: Dict[str, Any]) -> Dict[str, Any]:
    microscopy = dict(answers.get("microscopy", {}))
    medical = dict(answers.get("medical_3d", {}))
    return {
        "version": 1,
        "datasets": {
            "medical_3d": {
                "msd_task": {
                    "status": "CONFIGURED" if bool(medical.get("enabled", False)) else "NOT_CONFIGURED",
                    "task_name": medical.get("dataset_name", "NOT_CONFIGURED"),
                    "data_root": _common_root(medical.get("images_dir"), medical.get("masks_dir")),
                    "images_dir": medical.get("images_dir", "NOT_CONFIGURED"),
                    "masks_dir": medical.get("masks_dir", "NOT_CONFIGURED"),
                    "image_pattern": medical.get("image_pattern", "*.nii.gz"),
                    "mask_pattern": medical.get("mask_pattern", "*.nii.gz"),
                    "target_label": medical.get("target_label", 1),
                    "labels": "TO_BE_FILLED",
                    "split": "validation",
                    "source_url": "TO_BE_FILLED",
                    "license": "TO_BE_FILLED",
                    "citation": "TO_BE_FILLED",
                }
            },
            "microscopy": {
                "cellpose_or_bbbc": {
                    "status": "CONFIGURED" if bool(microscopy.get("enabled", False)) else "NOT_CONFIGURED",
                    "dataset_name": microscopy.get("dataset_name", "NOT_CONFIGURED"),
                    "data_root": _common_root(microscopy.get("images_dir"), microscopy.get("masks_dir")),
                    "images_dir": microscopy.get("images_dir", "NOT_CONFIGURED"),
                    "masks_dir": microscopy.get("masks_dir", "NOT_CONFIGURED"),
                    "image_pattern": microscopy.get("image_pattern", "*.png"),
                    "mask_pattern": microscopy.get("mask_pattern", "*.png"),
                    "instance_masks": bool(microscopy.get("instance_masks", True)),
                    "channels": microscopy.get("channels", [0, 0]),
                    "source_url": "TO_BE_FILLED",
                    "license": "TO_BE_FILLED",
                    "citation": "TO_BE_FILLED",
                }
            },
        },
    }


def build_experiment_registry(answers: Dict[str, Any]) -> Dict[str, Any]:
    microscopy = dict(answers.get("microscopy", {}))
    medical = dict(answers.get("medical_3d", {}))
    return {
        "version": 1,
        "experiments": {
            "microscopy_first_run": {
                "status": "CONFIGURED" if bool(microscopy.get("enabled", False)) else "NOT_CONFIGURED",
                "benchmark_config": "benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml",
                "output_dir": "results/real_microscopy_first_run",
                "max_cases": microscopy.get("max_cases", 10),
                "allow_classical_only": bool(microscopy.get("allow_classical_only", True)),
            },
            "medical_3d_first_run": {
                "status": "CONFIGURED" if bool(medical.get("enabled", False)) else "NOT_CONFIGURED",
                "benchmark_config": "benchmarks/configs/medical_3d_msd_local.template.yaml",
                "output_dir": "results/real_medical_3d_first_run",
                "max_cases": medical.get("max_cases", 5),
                "oracle_bbox_prompt": bool(medical.get("oracle_bbox_prompt", True)),
                "allow_classical_only": bool(medical.get("allow_classical_only", True)),
            },
        },
    }


def _external_model(backend: str, data: Dict[str, Any]) -> Dict[str, Any]:
    enabled = bool(data.get("enabled", False))
    return {
        "enabled": enabled,
        "backend_mode": "external_command",
        "command": data.get("command", "NOT_CONFIGURED"),
        "repo_path": data.get("repo_path", "NOT_CONFIGURED"),
        "checkpoint_path": data.get("checkpoint_path", "NOT_CONFIGURED"),
        "checkpoint_sha256": data.get("checkpoint_sha256", "NOT_CONFIGURED"),
        "source_url": data.get("source_url", "TO_BE_FILLED"),
        "license": data.get("license", "TO_BE_FILLED"),
        "device": data.get("device", "cpu"),
        "python_executable": data.get("python_executable", "NOT_CONFIGURED"),
        "status": "CONFIGURED" if enabled else "NOT_CONFIGURED",
    }


def _common_root(a: Any, b: Any) -> str:
    if not configured(a) or not configured(b):
        return "NOT_CONFIGURED"
    try:
        return os.path.commonpath([str(Path(a).resolve()), str(Path(b).resolve())])
    except Exception:
        return "NOT_CONFIGURED"


def dump_yaml(value: Any, indent: int = 0) -> str:
    lines = list(_dump_yaml_lines(value, indent))
    return "\n".join(lines) + "\n"


def _dump_yaml_lines(value: Any, indent: int = 0) -> Iterable[str]:
    pad = " " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                yield f"{pad}{key}:"
                yield from _dump_yaml_lines(item, indent + 2)
            else:
                yield f"{pad}{key}: {_scalar(item)}"
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                yield f"{pad}-"
                yield from _dump_yaml_lines(item, indent + 2)
            else:
                yield f"{pad}- {_scalar(item)}"
    else:
        yield f"{pad}{_scalar(value)}"


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "" or any(ch in text for ch in [":", "#", "[", "]", "{", "}", ","]) or text.lower() in {"true", "false", "null"}:
        return json.dumps(text)
    return json.dumps(text)


def next_commands() -> List[str]:
    return [
        "python -m app.configs.validate --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml",
        "python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment microscopy",
        "python -m app.experiments.preflight --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --experiment medical_3d",
        "python benchmarks/run_benchmark.py --config benchmarks/configs/microscopy_cellpose_or_bbbc_local.template.yaml --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --output results/real_microscopy_first_run",
        "python benchmarks/run_benchmark.py --config benchmarks/configs/medical_3d_msd_local.template.yaml --models configs/model_registry.local.yaml --datasets configs/datasets.local.yaml --output results/real_medical_3d_first_run",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
