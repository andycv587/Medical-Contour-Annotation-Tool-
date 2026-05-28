import json
import subprocess
import sys

import numpy as np

from segmentation.backends import ClassicalBackend, MockBackend, build_default_backends


def test_mock_backend_segments_2d():
    image = np.zeros((32, 32), dtype=np.uint8)
    image[8:20, 10:22] = 200
    result = MockBackend().segment(image, prompt="object")
    assert result.mask.shape == image.shape
    assert result.mask.sum() > 0


def test_classical_backend_segments_3d():
    image = np.zeros((3, 32, 32), dtype=np.uint8)
    image[:, 8:20, 10:22] = 200
    result = ClassicalBackend().segment(image, bbox=[8, 6, 24, 24])
    assert result.mask.shape == image.shape
    assert result.mask.sum() > 0


def test_backend_status_cli_json():
    completed = subprocess.run([sys.executable, "-m", "app.backends.check"], check=True, capture_output=True, text=True)
    data = json.loads(completed.stdout)
    assert "mock" in data
    assert data["mock"]["available"] is True


def test_default_backend_registry_contains_expected():
    names = set(build_default_backends())
    assert {"mock", "classical", "langsam", "medsam", "medsam2", "cellpose"}.issubset(names)
