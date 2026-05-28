import json

import nibabel as nib
import numpy as np

from contour_io.exporters import export_coco_json, export_nifti_mask, export_png_mask, export_polygon_json, export_tiff_stack


def test_export_formats(tmp_path):
    mask2d = np.zeros((16, 16), dtype=np.uint8)
    mask2d[4:10, 5:12] = 1
    png = tmp_path / "mask.png"
    export_png_mask(mask2d, str(png))
    assert png.exists()

    nii = tmp_path / "mask.nii.gz"
    export_nifti_mask(np.stack([mask2d, mask2d]), str(nii))
    assert nib.load(str(nii)).shape == (2, 16, 16)

    tif = tmp_path / "mask.tif"
    export_tiff_stack(np.stack([mask2d, mask2d]), str(tif))
    assert tif.exists()

    coco = tmp_path / "mask.json"
    export_coco_json(mask2d, str(coco))
    payload = json.loads(coco.read_text(encoding="utf-8"))
    assert payload["annotations"]

    poly = tmp_path / "polygons.json"
    export_polygon_json({0: [{"points": [[1, 1], [2, 1], [1, 2]], "label": "x"}]}, str(poly))
    assert json.loads(poly.read_text(encoding="utf-8"))["slices"][0]["slice_index"] == 0
