import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_HEAVY_TESTS") == "1":
        return
    skip_heavy = pytest.mark.skip(reason="set RUN_HEAVY_TESTS=1 to run heavy backend tests")
    for item in items:
        if "heavy" in item.keywords:
            item.add_marker(skip_heavy)
