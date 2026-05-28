import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image


def _force_repo_cache() -> None:
    root = Path(__file__).resolve().parents[2]
    cache = root / ".model_cache"
    (cache / "tmp").mkdir(parents=True, exist_ok=True)
    os_environ = __import__("os").environ
    os_environ.setdefault("HF_HOME", str(cache / "hf"))
    os_environ.setdefault("TORCH_HOME", str(cache / "torch"))
    os_environ.setdefault("XDG_CACHE_HOME", str(cache / "xdg"))
    os_environ.setdefault("TEMP", str(cache / "tmp"))
    os_environ.setdefault("TMP", str(cache / "tmp"))


def main() -> int:
    _force_repo_cache()
    parser = argparse.ArgumentParser(description="LangSAM external bridge for Medical Contour Annotation Tool.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", default="image", choices=["image", "volume"])
    args = parser.parse_args()
    if args.mode == "volume":
        print("LangSAM bridge currently supports 2D images only.", file=sys.stderr)
        return 2
    try:
        from lang_sam import LangSAM
    except Exception as ex:
        print(f"LangSAM is not importable in this Python environment: {ex}", file=sys.stderr)
        return 3

    image = np.load(args.input)
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    prompt = str(request.get("prompt", "")).strip()
    if not prompt:
        print("LangSAM bridge requires request.prompt.", file=sys.stderr)
        return 4
    if image.ndim != 2:
        print(f"LangSAM bridge expects a 2D image, got shape {image.shape}", file=sys.stderr)
        return 5

    model = LangSAM()
    pil = Image.fromarray(np.stack([image.astype(np.uint8)] * 3, axis=-1), mode="RGB")
    try:
        prediction = model.predict([pil], [prompt])
    except Exception:
        prediction = model.predict(pil, prompt)
    merged = _merge_masks(prediction, image.shape)
    np.save(args.output, merged.astype(np.uint8))
    return 0


def _merge_masks(prediction: Any, shape: tuple[int, int]) -> np.ndarray:
    merged = np.zeros(shape, dtype=np.uint8)
    for mask in _iter_masks(prediction):
        arr = np.asarray(mask)
        if arr.ndim > 2:
            arr = arr[..., 0]
        if arr.shape == shape:
            merged = np.maximum(merged, (arr > 0).astype(np.uint8))
    return merged


def _iter_masks(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        yield from value.get("masks", [])
    elif isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, dict):
                yield from item.get("masks", [])
            elif isinstance(item, (list, tuple)):
                yield from item
            else:
                yield item


if __name__ == "__main__":
    raise SystemExit(main())
