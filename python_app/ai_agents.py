import importlib
import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image


@dataclass
class AgentResult:
    masks: List[np.ndarray]
    message: str = ""


@dataclass
class AgentVolumeResult:
    mask_volume: Optional[np.ndarray]
    message: str = ""


class BaseSegmentationAgent:
    name = "base"

    def is_available(self) -> Tuple[bool, str]:
        raise NotImplementedError()

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        raise NotImplementedError()

    def supports_volume(self) -> bool:
        return False

    def predict_volume(self, volume_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentVolumeResult:
        _ = volume_u8
        _ = prompt
        _ = request
        return AgentVolumeResult(None, f"{self.name} does not support volume mode.")


class LangSAMAgent(BaseSegmentationAgent):
    name = "LangSAM"

    def __init__(self):
        self._model = None

    def is_available(self) -> Tuple[bool, str]:
        try:
            importlib.import_module("lang_sam")
            return True, "lang_sam available"
        except Exception as ex:
            return False, f"lang_sam not available: {ex}"

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        _ = request
        if not prompt.strip():
            return AgentResult([], "Prompt is empty.")
        try:
            mod = importlib.import_module("lang_sam")
            langsam_cls = getattr(mod, "LangSAM")
            if self._model is None:
                self._model = langsam_cls()
            model = self._model
            image_rgb = np.stack([image_gray_u8] * 3, axis=-1)
            pil = Image.fromarray(image_rgb, mode="RGB")
            # Compatible with different lang_sam versions:
            # - model.predict(image_pil, text_prompt)
            # - model.predict([image_pil], [text_prompt])
            try:
                result = model.predict([pil], [prompt])
            except Exception:
                result = model.predict(pil, prompt)

            masks = []
            if isinstance(result, (list, tuple)):
                if len(result) >= 1 and isinstance(result[0], (list, tuple, np.ndarray)):
                    masks = result[0]
                elif len(result) > 0 and isinstance(result[0], dict):
                    for item in result:
                        if "masks" in item:
                            masks.extend(item["masks"])
                else:
                    masks = result
            elif isinstance(result, dict) and "masks" in result:
                masks = result["masks"]

            out = []
            for m in masks:
                arr = np.asarray(m).astype(np.uint8)
                if arr.ndim > 2:
                    arr = arr[..., 0]
                out.append((arr > 0).astype(np.uint8))
            return AgentResult(out, f"LangSAM returned {len(out)} mask(s).")
        except Exception as ex:
            return AgentResult([], f"LangSAM inference failed: {ex}")


class MedSAMAgent(BaseSegmentationAgent):
    name = "MedSAM"

    def is_available(self) -> Tuple[bool, str]:
        cmd = os.environ.get("MEDSAM_INFER_CMD", "").strip()
        if cmd:
            return True, "external command bridge configured"
        try:
            importlib.import_module("medsam")
            return True, "medsam python package available"
        except Exception as ex:
            return False, (
                "medsam not available. Install medsam package OR set MEDSAM_INFER_CMD "
                f"for external bridge. Detail: {ex}"
            )

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        cmd = os.environ.get("MEDSAM_INFER_CMD", "").strip()
        if cmd:
            return self._predict_via_external_command(image_gray_u8=image_gray_u8, prompt=prompt, cmd=cmd, request=request or {})
        return AgentResult(
            [],
            "MedSAM package detected but direct runtime adapter is not wired in-app yet. "
            "Set MEDSAM_INFER_CMD to run external inference script.",
        )

    def _predict_via_external_command(self, image_gray_u8: np.ndarray, prompt: str, cmd: str, request: dict) -> AgentResult:
        # Protocol:
        # 1) write input npy + request json
        # 2) run external command:
        #    <cmd> --input <input.npy> --request <request.json> --output <output.npy>
        # 3) read output npy expected shape: (N,H,W) or (H,W)
        with tempfile.TemporaryDirectory(prefix="medsam_bridge_") as tmp_dir:
            input_npy = os.path.join(tmp_dir, "input.npy")
            request_json = os.path.join(tmp_dir, "request.json")
            output_npy = os.path.join(tmp_dir, "output.npy")
            np.save(input_npy, image_gray_u8.astype(np.uint8))
            with open(request_json, "w", encoding="utf-8") as f:
                payload = dict(request or {})
                payload["prompt"] = prompt
                json.dump(payload, f)
            try:
                cmd_parts = shlex.split(cmd, posix=False)
                if not cmd_parts:
                    return AgentResult([], "MEDSAM_INFER_CMD is empty after parsing.")
                completed = subprocess.run(
                    cmd_parts + ["--input", input_npy, "--request", request_json, "--output", output_npy],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
            except Exception as ex:
                return AgentResult([], f"MedSAM external bridge failed to start: {ex}")

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                msg = stderr if stderr else stdout
                return AgentResult([], f"MedSAM external bridge failed: {msg}")

            if not os.path.exists(output_npy):
                return AgentResult([], "MedSAM external bridge did not produce output.npy")

            try:
                masks = np.load(output_npy)
            except Exception as ex:
                return AgentResult([], f"MedSAM output read failed: {ex}")

            out: List[np.ndarray] = []
            if masks.ndim == 2:
                out.append((masks > 0).astype(np.uint8))
            elif masks.ndim == 3:
                for i in range(masks.shape[0]):
                    out.append((masks[i] > 0).astype(np.uint8))
            else:
                return AgentResult([], f"MedSAM output has invalid shape: {masks.shape}")
            return AgentResult(out, f"MedSAM bridge returned {len(out)} mask(s).")


class MedSAM2Agent(BaseSegmentationAgent):
    name = "MedSAM2"

    def is_available(self) -> Tuple[bool, str]:
        cmd = os.environ.get("MEDSAM2_INFER_CMD", "").strip()
        if cmd:
            return True, "external MedSAM2 volume bridge configured"
        try:
            importlib.import_module("medsam2")
            return True, "medsam2 python package available"
        except Exception as ex:
            return False, (
                "medsam2 not available. Install medsam2 package OR set MEDSAM2_INFER_CMD "
                f"for external bridge. Detail: {ex}"
            )

    def supports_volume(self) -> bool:
        return True

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        # Fallback for current-slice action: run volume mode on single-slice batch.
        vol = image_gray_u8[np.newaxis, ...]
        vr = self.predict_volume(vol, prompt, request=request)
        if vr.mask_volume is None:
            return AgentResult([], vr.message)
        if vr.mask_volume.ndim != 3 or vr.mask_volume.shape[0] < 1:
            return AgentResult([], f"MedSAM2 returned invalid single-slice volume shape: {vr.mask_volume.shape}")
        return AgentResult([(vr.mask_volume[0] > 0).astype(np.uint8)], vr.message)

    def predict_volume(self, volume_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentVolumeResult:
        cmd = os.environ.get("MEDSAM2_INFER_CMD", "").strip()
        if not cmd:
            return AgentVolumeResult(
                None,
                "MedSAM2 runtime adapter is not wired in-app. Set MEDSAM2_INFER_CMD to external volume bridge.",
            )

        with tempfile.TemporaryDirectory(prefix="medsam2_bridge_") as tmp_dir:
            input_npy = os.path.join(tmp_dir, "input_volume.npy")
            request_json = os.path.join(tmp_dir, "request.json")
            output_npy = os.path.join(tmp_dir, "output_volume.npy")
            np.save(input_npy, volume_u8.astype(np.uint8))

            payload = dict(request or {})
            payload["prompt"] = prompt
            seed_volume = payload.pop("seed_volume", None)
            if isinstance(seed_volume, np.ndarray):
                seed_path = os.path.join(tmp_dir, "seed_volume.npy")
                np.save(seed_path, seed_volume.astype(np.uint8))
                payload["seed_volume_path"] = seed_path
            with open(request_json, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            try:
                cmd_parts = shlex.split(cmd, posix=False)
                if not cmd_parts:
                    return AgentVolumeResult(None, "MEDSAM2_INFER_CMD is empty after parsing.")
                completed = subprocess.run(
                    cmd_parts + ["--mode", "volume", "--input", input_npy, "--request", request_json, "--output", output_npy],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
            except Exception as ex:
                return AgentVolumeResult(None, f"MedSAM2 external bridge failed to start: {ex}")

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                msg = stderr if stderr else stdout
                return AgentVolumeResult(None, f"MedSAM2 external bridge failed: {msg}")

            if not os.path.exists(output_npy):
                return AgentVolumeResult(None, "MedSAM2 external bridge did not produce output volume.")

            try:
                masks = np.load(output_npy)
            except Exception as ex:
                return AgentVolumeResult(None, f"MedSAM2 output read failed: {ex}")

            if masks.ndim == 4:
                masks = masks[0]
            if masks.ndim != 3:
                return AgentVolumeResult(None, f"MedSAM2 output has invalid shape: {masks.shape}")
            return AgentVolumeResult((masks > 0).astype(np.uint8), "MedSAM2 volume bridge returned mask volume.")


def build_agent_registry() -> Dict[str, BaseSegmentationAgent]:
    agents: Dict[str, BaseSegmentationAgent] = {}
    for cls in (LangSAMAgent, MedSAMAgent, MedSAM2Agent):
        inst = cls()
        agents[inst.name] = inst
    return agents
