import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np


def _force_repo_cache() -> None:
    root = Path(__file__).resolve().parents[2]
    cache = root / ".model_cache"
    (cache / "tmp").mkdir(parents=True, exist_ok=True)
    os_environ = __import__("os").environ
    os_environ.setdefault("HF_HOME", str(cache / "hf"))
    os_environ.setdefault("TORCH_HOME", str(cache / "torch"))
    os_environ.setdefault("XDG_CACHE_HOME", str(cache / "xdg"))
    os_environ.setdefault("CELLPOSE_LOCAL_MODELS_PATH", str(cache / "cellpose"))
    os_environ.setdefault("TEMP", str(cache / "tmp"))
    os_environ.setdefault("TMP", str(cache / "tmp"))


def main() -> int:
    _force_repo_cache()
    parser = argparse.ArgumentParser(description="Cellpose external bridge for Medical Contour Annotation Tool.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", default="image", choices=["image", "volume"])
    args = parser.parse_args()
    if args.mode == "volume":
        print("Cellpose bridge currently supports 2D images only.", file=sys.stderr)
        return 2
    try:
        from cellpose import models
    except Exception as ex:
        print(f"Cellpose is not importable in this Python environment: {ex}", file=sys.stderr)
        return 3

    image = np.load(args.input)
    request: Dict[str, Any] = json.loads(Path(args.request).read_text(encoding="utf-8"))
    if image.ndim != 2:
        print(f"Cellpose bridge expects a 2D image, got shape {image.shape}", file=sys.stderr)
        return 4
    use_gpu = str(request.get("device", "")).startswith("cuda") or bool(request.get("gpu", False))
    model = models.CellposeModel(gpu=use_gpu, model_type=request.get("model_type", "cyto"))
    masks, _flows, _styles = model.eval(
        image,
        diameter=request.get("diameter"),
        channels=request.get("channels", [0, 0]),
        flow_threshold=float(request.get("flow_threshold", 0.4)),
        cellprob_threshold=float(request.get("cellprob_threshold", 0.0)),
    )
    np.save(args.output, np.asarray(masks).astype(np.uint16))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
