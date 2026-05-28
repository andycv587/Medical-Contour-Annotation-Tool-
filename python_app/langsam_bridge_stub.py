import argparse
import json
import os
import sys

import cv2
import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="LangSAM external bridge stub.")
    parser.add_argument("--input", required=True, help="Path to input.npy (H, W) uint8")
    parser.add_argument("--request", required=True, help="Path to request.json")
    parser.add_argument("--output", required=True, help="Path to output.npy ((H, W) or (N, H, W))")
    return parser.parse_args()


def read_request(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def normalize(image_u8):
    lo, hi = np.percentile(image_u8, [1, 99])
    if hi <= lo:
        hi = lo + 1.0
    return np.clip((image_u8.astype(np.float32) - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def cell_like_masks(image_u8):
    img = normalize(image_u8)
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    n_labels, labels, stats, _centroids = cv2.connectedComponentsWithStats((binary > 0).astype(np.uint8), connectivity=8)
    masks = []
    min_area = max(8, image_u8.size // 5000)
    max_area = max(min_area + 1, image_u8.size // 5)
    for label in range(1, n_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if min_area <= area <= max_area:
            masks.append((labels == label).astype(np.uint8))
    if masks:
        return np.stack(masks, axis=0).astype(np.uint8)
    return (binary > 0).astype(np.uint8)


def semantic_mask(image_u8, prompt):
    p = (prompt or "").strip().lower()
    if any(token in p for token in ("cell", "cells", "nuclei", "nucleus", "dapi", "microscopy")):
        return cell_like_masks(image_u8)

    img = normalize(image_u8)
    if any(token in p for token in ("dark", "background", "vessel lumen")):
        img = 255 - img

    bias = 0.0
    if any(token in p for token in ("tumor", "lesion", "small")):
        bias = 8.0
    elif any(token in p for token in ("organ", "liver", "kidney", "spleen")):
        bias = -4.0
    thr = float(np.percentile(img, 65.0) + bias)
    mask = (img.astype(np.float32) >= thr).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask * 255, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return (mask > 0).astype(np.uint8)


def main():
    args = parse_args()
    try:
        image = np.load(args.input).astype(np.uint8)
    except Exception as ex:
        print(f"failed to load input npy: {ex}", file=sys.stderr)
        return 2
    if image.ndim != 2:
        print(f"input must be 2D (H, W), got shape={image.shape}", file=sys.stderr)
        return 3

    request = read_request(args.request)
    prompt = str(request.get("prompt", ""))
    try:
        mask = semantic_mask(image, prompt)
    except Exception as ex:
        print(f"stub inference failed: {ex}", file=sys.stderr)
        return 4

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    np.save(args.output, mask.astype(np.uint8))
    print(f"ok: wrote {args.output} shape={mask.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
