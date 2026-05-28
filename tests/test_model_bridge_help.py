import subprocess
import sys
from pathlib import Path


def test_model_bridge_help_commands():
    root = Path(__file__).resolve().parents[1]
    for name in ("cellpose_bridge.py", "langsam_bridge.py", "medsam_bridge.py", "medsam2_bridge.py"):
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / "model_bridges" / name), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0
        assert "--input" in completed.stdout
