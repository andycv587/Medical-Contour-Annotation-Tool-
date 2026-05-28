import argparse
import contextlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

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
    parser = argparse.ArgumentParser(
        description=(
            "MedSAM2 external bridge for 3D bbox-prompt propagation. If "
            "MEDSAM2_UPSTREAM_CMD is set, this delegates to that adapter; otherwise "
            "it runs the local MedSAM2/SAM2 predictor directly."
        )
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", default="volume", choices=["image", "volume"])
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    upstream = str(request.get("upstream_cmd") or os.environ.get("MEDSAM2_UPSTREAM_CMD", "")).strip()
    if not upstream:
        return _run_direct(args.input, request, args.output, args.mode)
    cmd = shlex.split(upstream, posix=False) + [
        "--input",
        args.input,
        "--request",
        args.request,
        "--output",
        args.output,
        "--mode",
        args.mode,
    ]
    completed = subprocess.run(cmd, check=False)
    return int(completed.returncode)


def _run_direct(input_path: str, request: dict, output_path: str, mode: str) -> int:
    if mode != "volume":
        print("MedSAM2 direct bridge expects --mode volume for 3D propagation.", file=sys.stderr)
        return 2
    volume = np.load(input_path)
    if volume.ndim != 3:
        print(f"MedSAM2 bridge expects a 3D volume, got shape {volume.shape}", file=sys.stderr)
        return 3
    checkpoint = _configured(request.get("checkpoint_path")) or _configured(os.environ.get("MEDSAM2_CHECKPOINT"))
    if not checkpoint or not Path(checkpoint).exists():
        print("MedSAM2 checkpoint_path is missing or does not exist.", file=sys.stderr)
        return 4
    repo_path = _configured(request.get("repo_path")) or _configured(os.environ.get("MEDSAM2_REPO_PATH"))
    if repo_path:
        sys.path.insert(0, repo_path)
    try:
        import torch
        from PIL import Image
        from sam2.build_sam import build_sam2_video_predictor_npz
    except Exception as ex:
        print(f"MedSAM2 dependencies are not importable in this Python environment: {ex}", file=sys.stderr)
        return 5
    try:
        device = str(request.get("device") or ("cuda" if torch.cuda.is_available() else "cpu"))
        cfg = str(request.get("cfg") or request.get("model_cfg") or "configs/sam2.1_hiera_t512.yaml")
        predictor = build_sam2_video_predictor_npz(cfg, checkpoint, device=device)
        axis = int(request.get("slice_axis", _shortest_axis(volume)))
        gt = _load_optional_array(request.get("oracle_gt_mask_path") or request.get("gt_mask_path"))
        if gt is not None and gt.shape != volume.shape:
            raise ValueError(f"oracle_gt_mask shape {gt.shape} does not match image shape {volume.shape}")
        seed_volume = _load_optional_array(request.get("seed_volume_path") or request.get("seed_mask_path"))
        if seed_volume is not None and seed_volume.shape != volume.shape:
            raise ValueError(f"seed_volume shape {seed_volume.shape} does not match image shape {volume.shape}")
        volume_dhw = np.moveaxis(volume, axis, 0).astype(np.uint8)
        gt_dhw = np.moveaxis(gt, axis, 0) if gt is not None else None
        seed_dhw = np.moveaxis(seed_volume, axis, 0) if seed_volume is not None else None
        if gt_dhw is not None:
            prompt_dhw = gt_dhw
            start, stop = _slice_bounds(gt_dhw, int(request.get("slice_margin", 0)))
        else:
            prompt_dhw = seed_dhw
            crop_to_seed = bool(request.get("crop_to_seed_bounds", False))
            if seed_dhw is not None and crop_to_seed:
                start, stop = _slice_bounds(seed_dhw, int(request.get("slice_margin", 0)))
            else:
                start, stop = 0, volume_dhw.shape[0]
        work = volume_dhw[start:stop]
        prompt_work = prompt_dhw[start:stop] if prompt_dhw is not None else None
        requested_key_frame = _optional_int(
            request.get("key_slice_index")
            or request.get("key_frame_index")
            or request.get("bbox_slice_index")
        )
        if requested_key_frame is not None:
            requested_key_frame -= start
        key_frame, bbox = _key_frame_and_bbox(work, prompt_work, request.get("bbox"), requested_key_frame=requested_key_frame)
        image_size = int(request.get("image_size", 512))
        video_height, video_width = int(work.shape[1]), int(work.shape[2])
        img_resized = _resize_grayscale_to_rgb_and_resize(work, image_size, Image)
        img_resized = torch.from_numpy(img_resized / 255.0).to(device=device, dtype=torch.float32)
        mean = torch.tensor((0.485, 0.456, 0.406), dtype=torch.float32, device=device)[:, None, None]
        std = torch.tensor((0.229, 0.224, 0.225), dtype=torch.float32, device=device)[:, None, None]
        img_resized = (img_resized - mean) / std
        seg_work = np.zeros(work.shape, dtype=np.uint8)
        autocast_ctx = torch.autocast("cuda", dtype=torch.bfloat16) if str(device).startswith("cuda") else contextlib.nullcontext()
        with torch.inference_mode(), autocast_ctx:
            inference_state = predictor.init_state(img_resized, video_height, video_width)
            predictor.add_new_points_or_box(inference_state=inference_state, frame_idx=key_frame, obj_id=1, box=np.asarray(bbox))
            for out_frame_idx, _out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state, start_frame_idx=key_frame, reverse=False):
                seg_work[out_frame_idx, (out_mask_logits[0] > 0.0).detach().cpu().numpy()[0]] = 1
            predictor.reset_state(inference_state)
            predictor.add_new_points_or_box(inference_state=inference_state, frame_idx=key_frame, obj_id=1, box=np.asarray(bbox))
            for out_frame_idx, _out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state, start_frame_idx=key_frame, reverse=True):
                seg_work[out_frame_idx, (out_mask_logits[0] > 0.0).detach().cpu().numpy()[0]] = 1
            predictor.reset_state(inference_state)
        out_dhw = np.zeros(volume_dhw.shape, dtype=np.uint8)
        out_dhw[start:stop] = seg_work
        out = np.moveaxis(out_dhw, 0, axis)
        np.save(output_path, out.astype(np.uint8))
        print(
            json.dumps(
                {
                    "mode": "direct",
                    "device": device,
                    "cfg": cfg,
                    "slice_axis": axis,
                    "slice_start": start,
                    "slice_stop": stop,
                    "processed_slices": int(stop - start),
                    "key_frame": int(key_frame + start),
                    "bbox": [int(x) for x in bbox],
                    "oracle_gt_mask_used": gt is not None,
                    "seed_volume_used": seed_volume is not None,
                },
                sort_keys=True,
            )
        )
        return 0
    except Exception as ex:
        print(f"MedSAM2 direct inference failed: {ex}", file=sys.stderr)
        return 6


def _configured(value) -> str | None:
    text = str(value or "").strip()
    if text in {"", "NOT_CONFIGURED", "TO_BE_FILLED", "TO_BE_CONFIGURED"}:
        return None
    return text


def _load_optional_array(path_value):
    path = _configured(path_value)
    if not path:
        return None
    return np.load(path)


def _shortest_axis(arr: np.ndarray) -> int:
    return int(np.argmin(arr.shape))


def _slice_bounds(gt_dhw: np.ndarray, margin: int) -> tuple[int, int]:
    nonempty = np.where(np.any(gt_dhw > 0, axis=(1, 2)))[0]
    if nonempty.size == 0:
        return 0, gt_dhw.shape[0]
    start = max(0, int(nonempty.min()) - max(0, margin))
    stop = min(gt_dhw.shape[0], int(nonempty.max()) + max(0, margin) + 1)
    return start, stop


def _key_frame_and_bbox(work: np.ndarray, gt_work, request_bbox, requested_key_frame=None) -> tuple[int, list[int]]:
    bbox = request_bbox if request_bbox and len(request_bbox) == 4 else None
    if bbox and requested_key_frame is not None:
        key_frame = max(0, min(int(work.shape[0] - 1), int(requested_key_frame)))
        return key_frame, [int(x) for x in bbox]
    if gt_work is not None and np.any(gt_work > 0):
        areas = np.count_nonzero(gt_work > 0, axis=(1, 2))
        if requested_key_frame is not None and 0 <= int(requested_key_frame) < gt_work.shape[0] and np.any(gt_work[int(requested_key_frame)] > 0):
            key_frame = int(requested_key_frame)
        else:
            key_frame = int(np.argmax(areas))
        bbox = _bbox_from_mask(gt_work[key_frame])
        if bbox:
            return key_frame, bbox
    if not bbox:
        raise ValueError("MedSAM2 direct bridge requires request.bbox or oracle_gt_mask for key-frame prompt generation")
    key_frame = int(requested_key_frame) if requested_key_frame is not None else work.shape[0] // 2
    key_frame = max(0, min(int(work.shape[0] - 1), key_frame))
    return key_frame, [int(x) for x in bbox]


def _optional_int(value) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _bbox_from_mask(mask: np.ndarray):
    ys, xs = np.where(np.asarray(mask) > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def _resize_grayscale_to_rgb_and_resize(array: np.ndarray, image_size: int, image_module) -> np.ndarray:
    d = int(array.shape[0])
    resized = np.zeros((d, 3, image_size, image_size), dtype=np.float32)
    for i in range(d):
        img = image_module.fromarray(array[i].astype(np.uint8)).convert("RGB")
        img = img.resize((image_size, image_size))
        resized[i] = np.asarray(img).transpose(2, 0, 1)
    return resized


if __name__ == "__main__":
    raise SystemExit(main())
