import argparse
import json
from typing import Any, Dict, List

from .io import find_not_configured, load_structured_config


def validate_configs(models_path: str, datasets_path: str, experiments_path: str = "") -> Dict[str, Any]:
    models = load_structured_config(models_path)
    datasets = load_structured_config(datasets_path)
    experiments = load_structured_config(experiments_path) if experiments_path else {}
    errors: List[str] = []
    if "models" not in models:
        errors.append("models config must contain a top-level 'models' mapping")
    if "datasets" not in datasets:
        errors.append("datasets config must contain a top-level 'datasets' mapping")
    if experiments_path and "experiments" not in experiments:
        errors.append("experiment config must contain a top-level 'experiments' mapping")
    return {
        "schema_valid": not errors,
        "errors": errors,
        "models_path": models_path,
        "datasets_path": datasets_path,
        "experiments_path": experiments_path or None,
        "not_configured_fields": {
            "models": find_not_configured(models),
            "datasets": find_not_configured(datasets),
            "experiments": find_not_configured(experiments) if experiments_path else [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local model/dataset/experiment configuration templates.")
    parser.add_argument("--models", required=True)
    parser.add_argument("--datasets", required=True)
    parser.add_argument("--experiments", default="")
    args = parser.parse_args()
    result = validate_configs(args.models, args.datasets, args.experiments)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["schema_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
