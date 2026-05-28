from typing import Dict, Optional

import cv2
import numpy as np


def binary_metrics(pred, gt) -> Dict[str, Optional[float]]:
    p = np.asarray(pred) > 0
    g = np.asarray(gt) > 0
    tp = int(np.count_nonzero(p & g))
    fp = int(np.count_nonzero(p & ~g))
    fn = int(np.count_nonzero(~p & g))
    denom_dice = 2 * tp + fp + fn
    denom_iou = tp + fp + fn
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    return {
        "dice": (2 * tp / denom_dice) if denom_dice else 1.0,
        "iou": (tp / denom_iou) if denom_iou else 1.0,
        "precision": precision,
        "recall": recall,
        "hausdorff95": hausdorff95(p, g),
    }


def hausdorff95(pred_bool, gt_bool) -> Optional[float]:
    try:
        from scipy.spatial.distance import cdist
    except Exception:
        return None
    p_pts = np.argwhere(pred_bool)
    g_pts = np.argwhere(gt_bool)
    if p_pts.size == 0 or g_pts.size == 0:
        return None
    if len(p_pts) > 5000:
        p_pts = p_pts[:: max(1, len(p_pts) // 5000)]
    if len(g_pts) > 5000:
        g_pts = g_pts[:: max(1, len(g_pts) // 5000)]
    d = cdist(p_pts, g_pts)
    forward = np.min(d, axis=1)
    backward = np.min(d, axis=0)
    return float(max(np.percentile(forward, 95), np.percentile(backward, 95)))


def instance_metrics(pred, gt, iou_threshold: float = 0.5) -> Dict[str, Optional[float]]:
    pred_labels = _labels(pred)
    gt_labels = _labels(gt)
    pred_ids = [int(v) for v in np.unique(pred_labels) if int(v) != 0]
    gt_ids = [int(v) for v in np.unique(gt_labels) if int(v) != 0]
    matched_gt = set()
    tp = 0
    for pid in pred_ids:
        p = pred_labels == pid
        best_iou = 0.0
        best_gid = None
        for gid in gt_ids:
            if gid in matched_gt:
                continue
            g = gt_labels == gid
            inter = np.count_nonzero(p & g)
            union = np.count_nonzero(p | g)
            iou = inter / union if union else 0.0
            if iou > best_iou:
                best_iou = iou
                best_gid = gid
        if best_iou >= iou_threshold and best_gid is not None:
            tp += 1
            matched_gt.add(best_gid)
    fp = len(pred_ids) - tp
    fn = len(gt_ids) - tp
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and (precision + recall) else None
    return {
        "object_precision": precision,
        "object_recall": recall,
        "object_f1": f1,
        "aji": None,
        "split_error": None,
        "merge_error": None,
        "pred_objects": len(pred_ids),
        "gt_objects": len(gt_ids),
    }


def _labels(mask):
    arr = np.asarray(mask)
    if arr.max(initial=0) > 1:
        return arr.astype(np.int32)
    n, labels = cv2.connectedComponents((arr > 0).astype(np.uint8), connectivity=8)
    _ = n
    return labels.astype(np.int32)
