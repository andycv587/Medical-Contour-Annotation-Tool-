import subprocess
import sys

from app.configs.io import load_structured_config


def test_create_local_config_from_answers_refuses_overwrite(tmp_path):
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        """
microscopy:
  enabled: true
  dataset_name: tiny_cells
  images_dir: images
  masks_dir: masks
  image_pattern: "*.png"
  mask_pattern: "*.png"
  instance_masks: true
  channels: [0, 0]
  max_cases: 2
medical_3d:
  enabled: false
  dataset_name: NOT_CONFIGURED
  images_dir: NOT_CONFIGURED
  masks_dir: NOT_CONFIGURED
  image_pattern: "*.nii.gz"
  mask_pattern: "*.nii.gz"
  target_label: 1
  max_cases: 1
  oracle_bbox_prompt: true
models:
  cellpose:
    enabled: false
    model_type: cyto
    diameter: null
    channels: [0, 0]
    device: cpu
  medsam:
    enabled: false
    command: NOT_CONFIGURED
    checkpoint_path: NOT_CONFIGURED
  medsam2:
    enabled: false
    command: NOT_CONFIGURED
    checkpoint_path: NOT_CONFIGURED
  langsam:
    enabled: false
    command: NOT_CONFIGURED
    checkpoint_path: NOT_CONFIGURED
""",
        encoding="utf-8",
    )
    out = tmp_path / "configs"
    cmd = [sys.executable, "scripts/create_local_config_from_answers.py", "--answers", str(answers), "--output-dir", str(out)]
    first = subprocess.run(cmd, capture_output=True, text=True)
    assert first.returncode == 0
    assert (out / "model_registry.local.yaml").exists()
    assert (out / "datasets.local.yaml").exists()
    generated = load_structured_config(str(out / "datasets.local.yaml"))
    assert generated["datasets"]["microscopy"]["cellpose_or_bbbc"]["dataset_name"] == "tiny_cells"
    second = subprocess.run(cmd, capture_output=True, text=True)
    assert second.returncode != 0


def test_create_local_config_force_overwrites(tmp_path):
    answers = "configs/andy_real_run_answers.template.yaml"
    out = tmp_path / "configs"
    cmd = [sys.executable, "scripts/create_local_config_from_answers.py", "--answers", answers, "--output-dir", str(out), "--force"]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    assert completed.returncode == 0
    models = load_structured_config(str(out / "model_registry.local.yaml"))
    assert "models" in models
