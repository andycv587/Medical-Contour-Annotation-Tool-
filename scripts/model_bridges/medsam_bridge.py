import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


def _force_repo_cache() -> None:
    root = Path(__file__).resolve().parents[2]
    cache = root / ".model_cache"
    (cache / "tmp").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache / "hf"))
    os.environ.setdefault("TORCH_HOME", str(cache / "torch"))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache / "xdg"))
    os.environ.setdefault("TEMP", str(cache / "tmp"))
    os.environ.setdefault("TMP", str(cache / "tmp"))


def main() -> int:
    _force_repo_cache()
    parser = argparse.ArgumentParser(description="MedSAM external bridge for 2D bbox-prompt segmentation.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", default="image", choices=["image", "volume"])
    args = parser.parse_args()
    image = np.load(args.input)
    request: Dict[str, Any] = json.loads(Path(args.request).read_text(encoding="utf-8"))
    if args.mode == "image":
        if image.ndim != 2:
            print(f"MedSAM bridge expects a 2D image, got shape {image.shape}", file=sys.stderr)
            return 3
        bbox = request.get("bbox")
        if not bbox or len(bbox) != 4:
            print("MedSAM bridge requires request.bbox = [x1, y1, x2, y2].", file=sys.stderr)
            return 4
    elif image.ndim != 3:
        print(f"MedSAM volume bridge expects a 3D image, got shape {image.shape}", file=sys.stderr)
        return 3

    repo_path = _configured(request.get("repo_path")) or _configured(os.environ.get("MEDSAM_REPO_PATH"))
    checkpoint = _configured(request.get("checkpoint_path")) or _configured(os.environ.get("MEDSAM_CHECKPOINT"))
    if repo_path:
        sys.path.insert(0, repo_path)
    if not checkpoint or not Path(checkpoint).exists():
        print("MedSAM checkpoint_path is missing or does not exist.", file=sys.stderr)
        return 5

    try:
        import torch
        from segment_anything import SamPredictor, sam_model_registry
    except Exception as ex:
        print(f"MedSAM dependencies are not importable in this Python environment: {ex}", file=sys.stderr)
        return 6

    try:
        device = request.get("device", "cuda:0" if torch.cuda.is_available() else "cpu")
        medsam = sam_model_registry["vit_b"](checkpoint=checkpoint)
        medsam.to(device=device)
        medsam.eval()
        predictor = SamPredictor(medsam)
        if args.mode == "volume":
            mask = _predict_volume(image, request, predictor)
        else:
            mask = _predict_slice(image, bbox, predictor)
    except Exception as ex:
        print(f"MedSAM inference failed: {ex}", file=sys.stderr)
        return 7
    np.save(args.output, mask.astype(np.uint8))
    return 0


def _configured(value: Optional[Any]) -> Optional[str]:
    text = str(value or "").strip()
    if text in {"", "NOT_CONFIGURED", "TO_BE_FILLED", "TO_BE_CONFIGURED"}:
        return None
    return text


def _predict_slice(image: np.ndarray, bbox, predictor) -> np.ndarray:
    rgb = np.stack([image.astype(np.uint8)] * 3, axis=-1)
    predictor.set_image(rgb)
    box = np.asarray(bbox, dtype=np.float32)
    masks, _scores, _logits = predictor.predict(box=box, multimask_output=False)
    return np.asarray(masks[0] if masks.ndim == 3 else masks) > 0


def _predict_volume(image: np.ndarray, request: Dict[str, Any], predictor) -> np.ndarray:
    axis = int(request.get("slice_axis", _shortest_axis(image)))
    gt = _load_optional_array(request.get("oracle_gt_mask_path") or request.get("gt_mask_path"))
    if gt is not None and gt.shape != image.shape:
        raise ValueError(f"oracle_gt_mask shape {gt.shape} does not match image shape {image.shape}")
    max_slices = _optional_int(request.get("max_slices") or request.get("max_oracle_slices"))
    out = np.zeros(image.shape, dtype=np.uint8)
    indices = _slice_indices(image, axis, gt)
    if max_slices is not None and max_slices > 0 and len(indices) > max_slices:
        chosen = np.linspace(0, len(indices) - 1, num=max_slices, dtype=int)
        indices = [indices[int(i)] for i in chosen]
    processed = 0
    skipped = 0
    for idx in indices:
        sl = np.take(image, idx, axis=axis)
        if gt is not None:
            gt_slice = np.take(gt, idx, axis=axis)
            bbox = _bbox_from_mask(gt_slice)
        else:
            bbox = request.get("bbox")
        if not bbox:
            skipped += 1
            continue
        pred = _predict_slice(sl, bbox, predictor).astype(np.uint8)
        _assign_slice(out, axis, idx, pred)
        processed += 1
    print(
        json.dumps(
            {
                "mode": "volume",
                "slice_axis": axis,
                "candidate_slices": len(indices),
                "processed_slices": processed,
                "skipped_slices": skipped,
                "oracle_gt_mask_used": gt is not None,
            },
            sort_keys=True,
        )
    )
    return out


def _load_optional_array(path_value) -> Optional[np.ndarray]:
    path = _configured(path_value)
    if not path:
        return None
    return np.load(path)


def _shortest_axis(arr: np.ndarray) -> int:
    return int(np.argmin(arr.shape))


def _slice_indices(image: np.ndarray, axis: int, gt: Optional[np.ndarray]) -> list[int]:
    if gt is None:
        return list(range(image.shape[axis]))
    other_axes = tuple(i for i in range(gt.ndim) if i != axis)
    nonempty = np.where(np.any(gt > 0, axis=other_axes))[0]
    return [int(i) for i in nonempty]


def _bbox_from_mask(mask: np.ndarray) -> Optional[list[int]]:
    ys, xs = np.where(np.asarray(mask) > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def _assign_slice(volume: np.ndarray, axis: int, idx: int, pred: np.ndarray) -> None:
    if axis == 0:
        volume[idx, :, :] = pred
    elif axis == 1:
        volume[:, idx, :] = pred
    elif axis == 2:
        volume[:, :, idx] = pred
    else:
        raise ValueError(f"unsupported slice axis: {axis}")


def _optional_int(value: Optional[Any]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
