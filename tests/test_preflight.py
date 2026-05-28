import numpy as np
from PIL import Image

from app.experiments.preflight import run_preflight


def test_preflight_template_fails_safely():
    result = run_preflight(
        models_path="configs/model_registry.local.template.yaml",
        datasets_path="configs/datasets.local.template.yaml",
        experiment="medical_3d",
    )
    assert result["ok"] is False
    assert result["missing"]


def test_preflight_passes_with_tiny_microscopy_pair(tmp_path):
    images = tmp_path / "images"
    masks = tmp_path / "masks"
    images.mkdir()
    masks.mkdir()
    image = np.zeros((10, 11), dtype=np.uint8)
    image[2:7, 3:8] = 200
    mask = (image > 0).astype(np.uint8)
    Image.fromarray(image).save(images / "case.png")
    Image.fromarray(mask).save(masks / "case.png")
    models = tmp_path / "models.yaml"
    datasets = tmp_path / "datasets.yaml"
    models.write_text(
        """
version: 1
models:
  classical:
    enabled: true
    backend_mode: internal
    status: CONFIGURED
  mock:
    enabled: false
    backend_mode: internal
    status: CONFIGURED
""",
        encoding="utf-8",
    )
    datasets.write_text(
        f"""
version: 1
datasets:
  microscopy:
    tiny:
      status: CONFIGURED
      dataset_name: tiny
      data_root: "{tmp_path}"
      images_dir: "{images}"
      masks_dir: "{masks}"
      image_pattern: "*.png"
      mask_pattern: "*.png"
      instance_masks: true
      source_url: "TO_BE_FILLED"
      license: "TO_BE_FILLED"
      citation: "TO_BE_FILLED"
""",
        encoding="utf-8",
    )
    result = run_preflight(models_path=str(models), datasets_path=str(datasets), experiment="microscopy", output_dir=str(tmp_path / "out"))
    assert result["ok"] is True
    assert "classical" in result["available_backends"]
