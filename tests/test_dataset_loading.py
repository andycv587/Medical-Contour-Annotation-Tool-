import numpy as np
import nibabel as nib
from PIL import Image

from benchmarks.datasets import load_medical_3d_cases, load_microscopy_cases


def test_medical_3d_loader_pairs_nifti(tmp_path):
    images = tmp_path / "images"
    masks = tmp_path / "masks"
    images.mkdir()
    masks.mkdir()
    image = np.zeros((4, 8, 9), dtype=np.float32)
    image[1:3, 2:6, 3:7] = 10
    mask = np.zeros((4, 8, 9), dtype=np.uint8)
    mask[1:3, 2:6, 3:7] = 2
    affine = np.eye(4)
    nib.save(nib.Nifti1Image(image, affine), images / "case001.nii.gz")
    nib.save(nib.Nifti1Image(mask, affine), masks / "case001.nii.gz")
    cases = load_medical_3d_cases(
        {
            "data_root": str(tmp_path),
            "images_dir": str(images),
            "masks_dir": str(masks),
            "image_pattern": "*.nii.gz",
            "mask_pattern": "*.nii.gz",
            "task_name": "tiny_msd",
        },
        target_label=2,
    )
    assert len(cases) == 1
    assert cases[0].case_id == "case001"
    assert cases[0].image_array.shape == mask.shape
    assert int(cases[0].gt_mask.sum()) == int(np.count_nonzero(mask == 2))
    assert "orientation_axcodes" in cases[0].metadata


def test_microscopy_loader_pairs_png(tmp_path):
    images = tmp_path / "images"
    masks = tmp_path / "masks"
    images.mkdir()
    masks.mkdir()
    img = np.zeros((12, 13, 3), dtype=np.uint8)
    img[3:8, 4:9, 1] = 220
    mask = np.zeros((12, 13), dtype=np.uint8)
    mask[3:8, 4:9] = 1
    Image.fromarray(img).save(images / "cell_a.png")
    Image.fromarray(mask).save(masks / "cell_a.png")
    cases = load_microscopy_cases(
        {
            "data_root": str(tmp_path),
            "images_dir": str(images),
            "masks_dir": str(masks),
            "image_pattern": "*.png",
            "mask_pattern": "*.png",
            "dataset_name": "tiny_cells",
            "instance_masks": True,
            "channel": 1,
        }
    )
    assert len(cases) == 1
    assert cases[0].case_id == "cell_a"
    assert cases[0].image_array.shape == mask.shape
    assert cases[0].gt_mask.shape == mask.shape
