import json
import os
from typing import Dict, List, Optional

import cv2
import nibabel as nib
import numpy as np
from PIL import Image


def export_png_mask(mask: np.ndarray, path: str) -> str:
    arr = _binary_u8(mask)
    if arr.ndim == 3:
        if arr.shape[0] != 1:
            raise ValueError("PNG export expects 2D mask or single-slice 3D mask")
        arr = arr[0]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    Image.fromarray(arr * 255, mode="L").save(path)
    return path


def export_nifti_mask(mask: np.ndarray, path: str, affine=None, header=None) -> str:
    arr = _binary_u8(mask)
    affine = np.eye(4) if affine is None else affine
    nii = nib.Nifti1Image(arr.astype(np.uint8), affine=affine, header=header)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    nib.save(nii, path)
    return path


def export_tiff_stack(mask: np.ndarray, path: str) -> str:
    arr = _binary_u8(mask)
    if arr.ndim == 2:
        frames = [Image.fromarray(arr * 255, mode="L")]
    elif arr.ndim == 3:
        frames = [Image.fromarray(sl.astype(np.uint8) * 255, mode="L") for sl in arr]
    else:
        raise ValueError(f"TIFF export expects 2D or 3D mask, got {arr.shape}")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:])
    return path


def export_polygon_json(polygons_by_slice: Dict[int, List[dict]], path: str, metadata: Optional[dict] = None) -> str:
    payload = {
        "version": 1,
        "metadata": metadata or {},
        "slices": [
            {"slice_index": int(z), "polygons": polygons}
            for z, polygons in sorted(polygons_by_slice.items(), key=lambda item: int(item[0]))
        ],
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return path


def export_coco_json(instance_mask: np.ndarray, path: str, image_id: int = 1, category_name: str = "object") -> str:
    arr = np.asarray(instance_mask)
    if arr.ndim != 2:
        raise ValueError("COCO export expects a 2D instance mask")
    h, w = arr.shape
    annotations = []
    ann_id = 1
    for value in sorted(int(v) for v in np.unique(arr) if int(v) != 0):
        binary = (arr == value).astype(np.uint8)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if contour.shape[0] < 3:
                continue
            segmentation = contour.reshape(-1, 2).astype(float).ravel().tolist()
            x, y, bw, bh = cv2.boundingRect(contour)
            area = float(cv2.contourArea(contour))
            annotations.append(
                {
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": 1,
                    "segmentation": [segmentation],
                    "area": area,
                    "bbox": [float(x), float(y), float(bw), float(bh)],
                    "iscrowd": 0,
                }
            )
            ann_id += 1
    payload = {
        "images": [{"id": image_id, "width": int(w), "height": int(h), "file_name": ""}],
        "annotations": annotations,
        "categories": [{"id": 1, "name": category_name}],
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return path


def _binary_u8(mask: np.ndarray) -> np.ndarray:
    return (np.asarray(mask) > 0).astype(np.uint8)
