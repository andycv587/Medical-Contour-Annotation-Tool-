import os
from typing import Tuple

import nibabel as nib
import numpy as np
from PIL import Image, ImageSequence


def load_image_or_volume(path: str) -> Tuple[np.ndarray, dict]:
    lower = path.lower()
    if lower.endswith(".nii") or lower.endswith(".nii.gz"):
        nii = nib.load(path)
        data = np.asarray(nii.get_fdata(dtype=np.float32))
        data = np.squeeze(data)
        if data.ndim != 3:
            raise ValueError(f"NIfTI loader expects 3D image, got {data.shape}")
        axis = int(np.argmin(np.array(data.shape)))
        data = np.moveaxis(data, axis, 0)
        return data.astype(np.float32), {"format": "nifti", "slice_axis": axis, "affine": nii.affine.tolist(), "filename": path}
    frames = []
    with Image.open(path) as img:
        for frame in ImageSequence.Iterator(img):
            frames.append(np.asarray(frame.convert("L"), dtype=np.float32))
    if not frames:
        raise ValueError(f"no frames loaded from {path}")
    shape = frames[0].shape
    if any(frame.shape != shape for frame in frames):
        raise ValueError("all image frames/pages must have same shape")
    return np.stack(frames, axis=0).astype(np.float32), {"format": os.path.splitext(path)[1].lstrip(".").lower(), "filename": path}
