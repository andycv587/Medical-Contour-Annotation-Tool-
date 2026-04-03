import argparse
import json
import os
import sys

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(
        description="MedSAM external bridge stub for ContourAnnotationApp."
    )
    parser.add_argument("--input", required=True, help="Path to input.npy (H, W) uint8")
    parser.add_argument(
        "--request",
        required=True,
        help="Path to request.json (contains optional prompt)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output.npy ((H, W) or (N, H, W), non-zero=foreground)",
    )
    return parser.parse_args()


def safe_read_request(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def stub_predict_mask(image_u8, prompt):
    # Simple deterministic placeholder:
    # - use percentile threshold to create one foreground mask
    # - prompt only influences threshold slightly for quick demo behavior
    p = (prompt or "").strip().lower()
    bias = 0.0
    if "tumor" in p or "lesion" in p:
        bias = -5.0
    elif "organ" in p or "liver" in p:
        bias = 5.0
    thr = float(np.percentile(image_u8, 70.0) + bias)
    mask = (image_u8.astype(np.float32) >= thr).astype(np.uint8)
    return mask


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        arr = np.load(args.input)
    except Exception as ex:
        print(f"failed to load input npy: {ex}", file=sys.stderr)
        return 3

    if arr.ndim != 2:
        print(f"input must be 2D (H, W), got shape={arr.shape}", file=sys.stderr)
        return 4

    image_u8 = arr.astype(np.uint8)
    request = safe_read_request(args.request)
    prompt = str(request.get("prompt", ""))

    try:
        mask = stub_predict_mask(image_u8=image_u8, prompt=prompt)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        np.save(args.output, mask.astype(np.uint8))
    except Exception as ex:
        print(f"stub inference failed: {ex}", file=sys.stderr)
        return 5

    print(f"ok: wrote mask to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
