import json
import subprocess
import sys

import numpy as np
from PIL import Image

from contour_io.importers import load_image_or_volume


def test_image_loader_png_and_tiff(tmp_path):
    arr = np.zeros((12, 14), dtype=np.uint8)
    arr[3:8, 4:9] = 200
    png = tmp_path / "img.png"
    Image.fromarray(arr).save(png)
    vol, meta = load_image_or_volume(str(png))
    assert vol.shape == (1, 12, 14)
    assert meta["format"] == "png"

    tif = tmp_path / "stack.tif"
    frames = [Image.fromarray(arr), Image.fromarray(arr + 1)]
    frames[0].save(tif, save_all=True, append_images=frames[1:])
    vol2, _ = load_image_or_volume(str(tif))
    assert vol2.shape == (2, 12, 14)


def test_cli_help_commands():
    completed = subprocess.run([sys.executable, "benchmarks/run_benchmark.py", "--help"], check=True, capture_output=True, text=True)
    assert "Run headless" in completed.stdout
    completed = subprocess.run([sys.executable, "experiments/run_ablation.py", "--help"], check=True, capture_output=True, text=True)
    assert "Run ablation" in completed.stdout
