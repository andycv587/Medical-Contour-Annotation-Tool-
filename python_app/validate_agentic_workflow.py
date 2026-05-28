import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

from agent_memory import AgenticMemory, compute_volume_signature
from ai_agents import AgenticWorkflowAgent, CellSegAgent, LangSAMAgent


def make_synthetic_volume(seed: int = 7):
    rng = np.random.default_rng(seed)
    z, h, w = 12, 96, 96
    zz, yy, xx = np.mgrid[:z, :h, :w]
    center = np.array([z * 0.52, h * 0.50, w * 0.47])
    radii = np.array([3.8, 24.0, 18.0])
    gt = (
        ((zz - center[0]) / radii[0]) ** 2
        + ((yy - center[1]) / radii[1]) ** 2
        + ((xx - center[2]) / radii[2]) ** 2
    ) <= 1.0

    volume = rng.normal(28, 5, size=(z, h, w)).astype(np.float32)
    volume += (yy / h * 12).astype(np.float32)
    volume[gt] = rng.normal(190, 10, size=int(np.count_nonzero(gt))).astype(np.float32)
    volume = np.clip(volume, 0, 255).astype(np.uint8)
    return volume, gt.astype(np.uint8)


def make_synthetic_cell_image(seed: int = 11):
    rng = np.random.default_rng(seed)
    h, w = 128, 128
    image = rng.normal(22, 4, size=(h, w)).astype(np.float32)
    gt = np.zeros((h, w), dtype=np.uint8)
    centers = []
    for _ in range(22):
        for _attempt in range(80):
            y = int(rng.integers(14, h - 14))
            x = int(rng.integers(14, w - 14))
            if all((x - cx) ** 2 + (y - cy) ** 2 > 13 ** 2 for cy, cx in centers):
                centers.append((y, x))
                break
    for y, x in centers:
        radius = int(rng.integers(5, 9))
        cv2.circle(gt, (x, y), radius, 1, -1)
        cv2.circle(image, (x, y), radius, float(rng.normal(190, 14)), -1)
        cv2.circle(image, (x, y), max(1, radius // 2), float(rng.normal(230, 10)), -1)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    image += rng.normal(0, 5, size=(h, w)).astype(np.float32)
    return np.clip(image, 0, 255).astype(np.uint8), gt


def bbox_from_mask(mask):
    ys, xs = np.where(mask > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def dice_score(pred, gt):
    pred = pred > 0
    gt = gt > 0
    denom = int(np.count_nonzero(pred) + np.count_nonzero(gt))
    if denom == 0:
        return 1.0
    return float(2.0 * np.count_nonzero(pred & gt) / denom)


def merge_masks(masks, shape):
    merged = np.zeros(shape, dtype=np.uint8)
    for mask in masks:
        if mask is not None and mask.shape == shape:
            merged = np.maximum(merged, (mask > 0).astype(np.uint8))
    return merged


def main():
    app_dir = Path(__file__).resolve().parent
    langsam_cmd = subprocess.list2cmdline([sys.executable, str(app_dir / "langsam_bridge_stub.py")])
    medsam_cmd = subprocess.list2cmdline([sys.executable, str(app_dir / "medsam_bridge_stub.py")])
    medsam2_cmd = subprocess.list2cmdline([sys.executable, str(app_dir / "medsam2_bridge_stub.py")])
    os.environ["LANGSAM_INFER_CMD"] = langsam_cmd
    os.environ["MEDSAM_INFER_CMD"] = medsam_cmd
    os.environ["MEDSAM2_INFER_CMD"] = medsam2_cmd
    os.environ.pop("AGENT_ROUTER_CMD", None)

    volume, gt = make_synthetic_volume()
    z_mid = volume.shape[0] // 2
    seed_volume = np.zeros_like(volume, dtype=np.uint8)
    for z in (z_mid - 2, z_mid + 2):
        seed_volume[z] = gt[z]
    bbox = bbox_from_mask(gt[z_mid])
    if bbox is None:
        raise AssertionError("synthetic ground-truth bbox was empty")

    agent = AgenticWorkflowAgent()
    ok, detail = agent.is_available()
    if not ok:
        raise AssertionError(f"AgenticWorkflow not available: {detail}")

    request = {
        "seed_mode": "3d",
        "seed_volume": seed_volume,
        "bbox": bbox,
        "bbox_slice_index": z_mid,
        "use_langsam_seeds": False,
    }
    start = time.perf_counter()
    result = agent.predict_volume(volume, "liver lesion", request=request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if result.mask_volume is None:
        raise AssertionError(result.message)
    if result.mask_volume.shape != volume.shape:
        raise AssertionError(f"invalid mask shape {result.mask_volume.shape}, expected {volume.shape}")
    if not np.any(result.mask_volume > 0):
        raise AssertionError("workflow produced an empty 3D mask")

    dice = dice_score(result.mask_volume, gt)
    if dice < 0.35:
        raise AssertionError(f"synthetic Dice too low: {dice:.3f}")

    slice_coverage = int(np.count_nonzero(np.any(result.mask_volume > 0, axis=(1, 2))))
    if slice_coverage < 4:
        raise AssertionError(f"insufficient 3D slice coverage: {slice_coverage}")

    with tempfile.TemporaryDirectory(prefix="mcat_memory_validation_") as tmp_dir:
        memory_path = os.path.join(tmp_dir, "agent_memory.json")
        memory = AgenticMemory(long_term_path=memory_path)
        signature = compute_volume_signature(volume, "synthetic_liver.nii.gz")
        memory.record(
            signature,
            "liver lesion",
            "AgenticWorkflow",
            "volume",
            "validation",
            mask_volume=result.mask_volume,
            elapsed_ms=elapsed_ms,
            message=result.message,
            persist=True,
        )

        reloaded_memory = AgenticMemory(long_term_path=memory_path)
        memory_hit = reloaded_memory.suggest_bbox(
            signature,
            "liver lesion",
            slice_index=z_mid,
            use_short_term=False,
            use_long_term=True,
        )
        if not memory_hit or not memory_hit.get("bbox"):
            raise AssertionError("long-term memory did not return a bbox")

        slice_result = agent.predict(volume[z_mid], "liver lesion", request={"memory_bbox": memory_hit["bbox"]})
        if not slice_result.masks:
            raise AssertionError("memory-guided slice workflow produced no masks")

    langsam = LangSAMAgent()
    langsam_result = langsam.predict(volume[z_mid], "liver lesion")
    if not langsam_result.masks:
        raise AssertionError("LangSAM bridge produced no masks")

    cell_image, cell_gt = make_synthetic_cell_image()
    cell_agent = CellSegAgent()
    cell_result = cell_agent.predict(cell_image, "cells nuclei", request={"min_cell_area": 40})
    cell_merged = merge_masks(cell_result.masks, cell_image.shape)
    cell_dice = dice_score(cell_merged, cell_gt)
    if len(cell_result.masks) < 10:
        raise AssertionError(f"CellSeg found too few cells: {len(cell_result.masks)}")
    if cell_dice < 0.65:
        raise AssertionError(f"CellSeg synthetic Dice too low: {cell_dice:.3f}")

    routed_cell = agent.predict(cell_image, "segment cells and nuclei", request={})
    if not routed_cell.masks:
        raise AssertionError("AgenticWorkflow did not route cell prompt to a working cell segmentation path")

    report = {
        "status": "ok",
        "agent_available": detail,
        "workflow_message": result.message,
        "langsam_message": langsam_result.message,
        "cellseg_message": cell_result.message,
        "routed_cell_message": routed_cell.message,
        "volume_shape": list(volume.shape),
        "dice_synthetic": round(dice, 4),
        "cell_dice_synthetic": round(cell_dice, 4),
        "cell_instances": len(cell_result.masks),
        "mask_voxels": int(np.count_nonzero(result.mask_volume)),
        "slice_coverage": slice_coverage,
        "elapsed_ms": round(elapsed_ms, 2),
        "memory_bbox": memory_hit["bbox"],
        "slice_masks": len(slice_result.masks),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
