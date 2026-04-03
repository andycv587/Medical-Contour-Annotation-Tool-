import argparse
import json
import os
import sys

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="MedSAM2 volume bridge stub.")
    parser.add_argument("--mode", default="volume", choices=["volume"])
    parser.add_argument("--input", required=True, help="input volume npy: (Z,H,W) uint8")
    parser.add_argument("--request", required=True, help="request json")
    parser.add_argument("--output", required=True, help="output volume npy: (Z,H,W) uint8")
    return parser.parse_args()


def read_request(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def ensure_volume(arr):
    if arr.ndim != 3:
        raise ValueError(f"expected volume (Z,H,W), got {arr.shape}")
    return arr.astype(np.uint8)


def sanitize_bbox(bbox, h, w):
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    try:
        x1, y1, x2, y2 = [int(v) for v in bbox]
    except Exception:
        return None
    x1 = max(0, min(w - 1, x1))
    x2 = max(0, min(w - 1, x2))
    y1 = max(0, min(h - 1, y1))
    y2 = max(0, min(h - 1, y2))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    if x2 == x1 or y2 == y1:
        return None
    return [x1, y1, x2, y2]


def bbox_to_mask(bbox, h, w):
    b = sanitize_bbox(bbox, h, w)
    if b is None:
        return np.zeros((h, w), dtype=np.uint8)
    x1, y1, x2, y2 = b
    m = np.zeros((h, w), dtype=np.uint8)
    m[y1:y2 + 1, x1:x2 + 1] = 1
    return m


def build_bbox_roi_volume(z, h, w, request):
    bbox = request.get("bbox")
    if bbox is None:
        return np.zeros((z, h, w), dtype=np.uint8)
    base = bbox_to_mask(bbox, h, w)
    if not np.any(base):
        return np.zeros((z, h, w), dtype=np.uint8)

    # Optional slice-anchor taper: strongest around bbox_slice_index.
    center = request.get("bbox_slice_index")
    roi = np.zeros((z, h, w), dtype=np.uint8)
    if center is None:
        for i in range(z):
            roi[i] = base
        return roi
    try:
        center = int(center)
    except Exception:
        center = 0
    center = max(0, min(z - 1, center))
    for i in range(z):
        dist = abs(i - center)
        # Decay ROI with distance but keep non-zero support across volume.
        if dist <= 2:
            roi[i] = base
        elif dist <= 6:
            roi[i] = base
        else:
            roi[i] = base
    return roi


def load_seed_volume(z, h, w, request):
    seed_path = request.get("seed_volume_path")
    if not isinstance(seed_path, str) or not os.path.exists(seed_path):
        return None
    try:
        seed = np.load(seed_path).astype(np.uint8)
    except Exception:
        return None
    if seed.shape != (z, h, w):
        return None
    return (seed > 0).astype(np.uint8)


def infer_slice_with_roi(sl_u8, roi_u8, fallback_percentile=70.0):
    sl = sl_u8.astype(np.float32)
    if roi_u8 is not None and np.any(roi_u8 > 0):
        local = sl[roi_u8 > 0]
        if local.size > 0:
            thr = float(np.percentile(local, 60.0))
            m = (sl >= thr).astype(np.uint8)
            return (m * (roi_u8 > 0).astype(np.uint8)).astype(np.uint8)
    thr = float(np.percentile(sl, fallback_percentile))
    return (sl >= thr).astype(np.uint8)


def simple_volume_predict(volume_u8, request):
    z, h, w = volume_u8.shape
    out = np.zeros((z, h, w), dtype=np.uint8)

    seed = load_seed_volume(z, h, w, request)
    bbox_roi = build_bbox_roi_volume(z, h, w, request)

    if seed is not None:
        # Hybrid ROI = seed slice if present, else fallback to bbox ROI.
        for i in range(z):
            roi = seed[i]
            if not np.any(roi) and np.any(bbox_roi[i]):
                roi = bbox_roi[i]
            out[i] = infer_slice_with_roi(volume_u8[i], roi, fallback_percentile=70.0)
        return out

    if np.any(bbox_roi):
        for i in range(z):
            out[i] = infer_slice_with_roi(volume_u8[i], bbox_roi[i], fallback_percentile=70.0)
        return out

    for i in range(z):
        out[i] = infer_slice_with_roi(volume_u8[i], None, fallback_percentile=70.0)
    return out


def main():
    args = parse_args()
    try:
        vol = ensure_volume(np.load(args.input))
    except Exception as ex:
        print(f"failed reading input volume: {ex}", file=sys.stderr)
        return 2

    request = read_request(args.request)
    try:
        pred = simple_volume_predict(vol, request)
    except Exception as ex:
        print(f"inference failed: {ex}", file=sys.stderr)
        return 3

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    np.save(args.output, pred.astype(np.uint8))
    print(f"ok: wrote {args.output} shape={pred.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
