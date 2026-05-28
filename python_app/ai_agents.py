import importlib
import json
import os
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


@dataclass
class AgentResult:
    masks: List[np.ndarray]
    message: str = ""
    routing: Optional[Dict[str, Any]] = None


@dataclass
class AgentVolumeResult:
    mask_volume: Optional[np.ndarray]
    message: str = ""
    routing: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowPlan:
    scope: str
    backend: str
    route: str
    reason: str
    used_router: str = "heuristic"
    seed_sources: Optional[List[str]] = None

    def message(self) -> str:
        parts = [f"route={self.route}", f"backend={self.backend}", f"router={self.used_router}", self.reason]
        if self.seed_sources:
            parts.append("seeds=" + ",".join(self.seed_sources))
        return " | ".join(parts)

    def to_routing_dict(self, available: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        available = available or {}
        unavailable = {
            name: info.get("detail", "")
            for name, info in available.items()
            if not info.get("ok", False)
        }
        ranked = [self.backend] if self.backend and self.backend != "none" else []
        for name in ("CellSeg", "LangSAM", "MedSAM", "MedSAM2"):
            if name not in ranked:
                ranked.append(name)
        return {
            "selected_backend": self.backend,
            "ranked_candidates": ranked,
            "unavailable_backends": unavailable,
            "fallback_history": [],
            "prompt_interpretation": {},
            "image_type_guess": "volume" if self.scope == "volume" else "slice",
            "decision_reason": self.reason,
            "route": self.route,
            "router": self.used_router,
            "seed_sources": list(self.seed_sources or []),
        }


def _split_command(cmd: str) -> List[str]:
    try:
        parts = shlex.split(cmd, posix=False)
    except Exception:
        parts = cmd.split()
    cleaned = []
    for part in parts:
        p = part.strip()
        if len(p) >= 2 and ((p[0] == p[-1] == '"') or (p[0] == p[-1] == "'")):
            p = p[1:-1]
        if p:
            cleaned.append(p)
    return cleaned


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


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
        cmd = os.environ.get("LANGSAM_INFER_CMD", "").strip()
        if cmd:
            return True, "external LangSAM command bridge configured"
        try:
            importlib.import_module("lang_sam")
            return True, "lang_sam available"
        except Exception as ex:
            return False, (
                "lang_sam not available. Install lang-segment-anything OR set LANGSAM_INFER_CMD "
                f"for external bridge. Detail: {ex}"
            )

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        if not prompt.strip():
            return AgentResult([], "Prompt is empty.")
        cmd = os.environ.get("LANGSAM_INFER_CMD", "").strip()
        if cmd:
            return self._predict_via_external_command(image_gray_u8, prompt, cmd, request or {})
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

    def _predict_via_external_command(self, image_gray_u8: np.ndarray, prompt: str, cmd: str, request: dict) -> AgentResult:
        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="langsam_bridge_") as tmp_dir:
            input_npy = os.path.join(tmp_dir, "input.npy")
            request_json = os.path.join(tmp_dir, "request.json")
            output_npy = os.path.join(tmp_dir, "output.npy")
            np.save(input_npy, image_gray_u8.astype(np.uint8))
            payload = dict(request or {})
            payload["prompt"] = prompt
            with open(request_json, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            try:
                cmd_parts = _split_command(cmd)
                if not cmd_parts:
                    return AgentResult([], "LANGSAM_INFER_CMD is empty after parsing.")
                completed = subprocess.run(
                    cmd_parts + ["--input", input_npy, "--request", request_json, "--output", output_npy],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
            except Exception as ex:
                return AgentResult([], f"LangSAM external bridge failed to start: {ex}")

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                stdout = (completed.stdout or "").strip()
                msg = stderr if stderr else stdout
                return AgentResult([], f"LangSAM external bridge failed: {msg}")

            if not os.path.exists(output_npy):
                return AgentResult([], "LangSAM external bridge did not produce output.npy")

            try:
                masks = np.load(output_npy)
            except Exception as ex:
                return AgentResult([], f"LangSAM output read failed: {ex}")

            out: List[np.ndarray] = []
            if masks.ndim == 2:
                out.append((masks > 0).astype(np.uint8))
            elif masks.ndim == 3:
                for i in range(masks.shape[0]):
                    out.append((masks[i] > 0).astype(np.uint8))
            else:
                return AgentResult([], f"LangSAM output has invalid shape: {masks.shape}")
            return AgentResult(out, f"LangSAM bridge returned {len(out)} mask(s) in {_elapsed_ms(start):.1f} ms.")


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
        start = time.perf_counter()
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
                cmd_parts = _split_command(cmd)
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
            return AgentResult(out, f"MedSAM bridge returned {len(out)} mask(s) in {_elapsed_ms(start):.1f} ms.")


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

        start = time.perf_counter()
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
                cmd_parts = _split_command(cmd)
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
            return AgentVolumeResult((masks > 0).astype(np.uint8), f"MedSAM2 volume bridge returned mask volume in {_elapsed_ms(start):.1f} ms.")


class CellSegAgent(BaseSegmentationAgent):
    name = "CellSeg"

    def is_available(self) -> Tuple[bool, str]:
        return True, "built-in OpenCV microscopy cell segmentation available"

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        start = time.perf_counter()
        req = request or {}
        image = np.asarray(image_gray_u8)
        if image.ndim != 2:
            return AgentResult([], f"CellSeg expects a 2D grayscale image, got {image.shape}")
        image = np.nan_to_num(image, nan=0, posinf=255, neginf=0).astype(np.uint8)
        masks, mode_message = self._segment_cells(image, prompt, req)
        return AgentResult(masks, f"CellSeg returned {len(masks)} cell mask(s) via {mode_message} in {_elapsed_ms(start):.1f} ms.")

    def _segment_cells(self, image_u8: np.ndarray, prompt: str, request: Dict[str, Any]) -> Tuple[List[np.ndarray], str]:
        p = (prompt or "").lower()
        min_area = int(request.get("min_cell_area", request.get("min_area", 20)))
        max_area = int(request.get("max_cell_area", max(80, image_u8.size // 3)))
        max_instances = int(request.get("max_cell_instances", 512))
        min_area = max(3, min_area)
        max_area = max(min_area + 1, max_area)

        enhanced = self._enhance_cell_image(image_u8)
        prefer_dark = any(token in p for token in ("dark", "brightfield", "phase", "hematoxylin", "h&e", "he "))
        candidates = []
        if prefer_dark:
            candidates.append(("dark-object watershed", 255 - enhanced))
            candidates.append(("bright-object watershed", enhanced))
        else:
            candidates.append(("bright-object watershed", enhanced))
            candidates.append(("dark-object watershed", 255 - enhanced))

        best_masks: List[np.ndarray] = []
        best_name = candidates[0][0]
        best_score = -1
        for name, work in candidates:
            binary = self._threshold_cells(work)
            masks = self._watershed_instances(work, binary, min_area=min_area, max_area=max_area, max_instances=max_instances)
            score = self._cell_score(masks, image_u8.shape)
            if score > best_score:
                best_score = score
                best_masks = masks
                best_name = name

        if not best_masks:
            binary = self._adaptive_cells(enhanced)
            best_masks = self._component_instances(binary, min_area=min_area, max_area=max_area, max_instances=max_instances)
            best_name = "adaptive connected-components"
        return best_masks, best_name

    @staticmethod
    def _enhance_cell_image(image_u8: np.ndarray) -> np.ndarray:
        lo, hi = np.percentile(image_u8, [1, 99])
        if hi <= lo:
            hi = lo + 1.0
        norm = np.clip((image_u8.astype(np.float32) - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(norm)

    @staticmethod
    def _threshold_cells(work_u8: np.ndarray) -> np.ndarray:
        blur = cv2.GaussianBlur(work_u8, (5, 5), 0)
        _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, kernel, iterations=1)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
        return closed

    @staticmethod
    def _adaptive_cells(work_u8: np.ndarray) -> np.ndarray:
        block = max(15, (min(work_u8.shape) // 12) | 1)
        binary = cv2.adaptiveThreshold(
            work_u8,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block,
            -2,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    def _watershed_instances(
        self,
        work_u8: np.ndarray,
        binary_u8: np.ndarray,
        *,
        min_area: int,
        max_area: int,
        max_instances: int,
    ) -> List[np.ndarray]:
        if not np.any(binary_u8 > 0):
            return []
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        sure_bg = cv2.dilate(binary_u8, kernel, iterations=2)
        dist = cv2.distanceTransform((binary_u8 > 0).astype(np.uint8), cv2.DIST_L2, 5)
        max_dist = float(dist.max())
        if max_dist <= 0:
            return self._component_instances(binary_u8, min_area=min_area, max_area=max_area, max_instances=max_instances)
        _, sure_fg = cv2.threshold(dist, 0.35 * max_dist, 255, 0)
        sure_fg = sure_fg.astype(np.uint8)
        unknown = cv2.subtract(sure_bg, sure_fg)
        n_labels, markers = cv2.connectedComponents(sure_fg)
        if n_labels <= 1:
            return self._component_instances(binary_u8, min_area=min_area, max_area=max_area, max_instances=max_instances)
        markers = markers + 1
        markers[unknown > 0] = 0
        color = cv2.cvtColor(work_u8, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(color, markers)
        masks = []
        for label in range(2, int(markers.max()) + 1):
            mask = (markers == label).astype(np.uint8)
            cleaned = cv2.morphologyEx(mask * 255, cv2.MORPH_OPEN, kernel, iterations=1)
            if self._accept_cell_mask(cleaned, min_area, max_area):
                masks.append((cleaned > 0).astype(np.uint8))
                if len(masks) >= max_instances:
                    break
        if not masks:
            return self._component_instances(binary_u8, min_area=min_area, max_area=max_area, max_instances=max_instances)
        return masks

    def _component_instances(self, binary_u8: np.ndarray, *, min_area: int, max_area: int, max_instances: int) -> List[np.ndarray]:
        n_labels, labels, stats, _centroids = cv2.connectedComponentsWithStats((binary_u8 > 0).astype(np.uint8), connectivity=8)
        masks = []
        for label in range(1, n_labels):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < min_area or area > max_area:
                continue
            mask = (labels == label).astype(np.uint8)
            if self._accept_cell_mask(mask * 255, min_area, max_area):
                masks.append(mask)
                if len(masks) >= max_instances:
                    break
        return masks

    @staticmethod
    def _accept_cell_mask(mask_u8: np.ndarray, min_area: int, max_area: int) -> bool:
        area = int(np.count_nonzero(mask_u8))
        if area < min_area or area > max_area:
            return False
        contours, _ = cv2.findContours((mask_u8 > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        perimeter = max(cv2.arcLength(c, True) for c in contours)
        if perimeter <= 0:
            return True
        circularity = float(4.0 * np.pi * area / (perimeter * perimeter))
        return circularity >= 0.08

    @staticmethod
    def _cell_score(masks: List[np.ndarray], shape: Tuple[int, int]) -> float:
        if not masks:
            return -1.0
        areas = np.array([np.count_nonzero(m) for m in masks], dtype=np.float32)
        coverage = float(np.sum(areas) / max(1, shape[0] * shape[1]))
        if coverage <= 0.001 or coverage > 0.85:
            return -1.0
        area_cv = float(np.std(areas) / max(1.0, np.mean(areas)))
        return len(masks) - area_cv


class AgenticTaskRouter:
    """Deterministic router with an optional external VLM/LLM planner hook."""

    CELL_PROMPT_TOKENS = (
        "cell",
        "cells",
        "nuclei",
        "nucleus",
        "microscopy",
        "dapi",
        "fluorescence",
        "brightfield",
        "phase",
        "cytoplasm",
        "hela",
        "neuron",
    )

    def plan(
        self,
        scope: str,
        prompt: str,
        request: Dict[str, Any],
        agents: Dict[str, BaseSegmentationAgent],
    ) -> WorkflowPlan:
        request = dict(request or {})
        request["prompt"] = prompt
        available = self._available_agents(agents)
        external = os.environ.get("AGENT_ROUTER_CMD", "").strip()
        if external:
            plan = self._plan_via_external_router(external, scope, prompt, request, available)
            if plan and (plan.backend == "none" or available.get(plan.backend, {}).get("ok", False)):
                return plan
        return self._heuristic_plan(scope, request, available)

    @staticmethod
    def _available_agents(agents: Dict[str, BaseSegmentationAgent]) -> Dict[str, Dict[str, Any]]:
        info: Dict[str, Dict[str, Any]] = {}
        for name, agent in agents.items():
            try:
                ok, detail = agent.is_available()
            except Exception as ex:
                ok, detail = False, str(ex)
            info[name] = {
                "ok": bool(ok),
                "detail": detail,
                "supports_volume": bool(agent.supports_volume()),
            }
        return info

    def _plan_via_external_router(
        self,
        cmd: str,
        scope: str,
        prompt: str,
        request: Dict[str, Any],
        available: Dict[str, Dict[str, Any]],
    ) -> Optional[WorkflowPlan]:
        with tempfile.TemporaryDirectory(prefix="agent_router_") as tmp_dir:
            input_json = os.path.join(tmp_dir, "router_request.json")
            output_json = os.path.join(tmp_dir, "router_plan.json")
            payload = {
                "scope": scope,
                "prompt": prompt,
                "available": available,
                "features": self._request_features(request),
            }
            try:
                with open(input_json, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                cmd_parts = _split_command(cmd)
                if not cmd_parts:
                    return None
                completed = subprocess.run(
                    cmd_parts + ["--input", input_json, "--output", output_json],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if completed.returncode != 0 or not os.path.exists(output_json):
                    return None
                with open(output_json, "r", encoding="utf-8") as f:
                    raw = json.load(f)
            except Exception:
                return None
        if not isinstance(raw, dict):
            return None
        backend = str(raw.get("backend", "")).strip()
        route = str(raw.get("route", backend or "external")).strip() or "external"
        reason = str(raw.get("reason", "external router decision")).strip()
        seeds = raw.get("seed_sources", [])
        if not isinstance(seeds, list):
            seeds = []
        if backend not in available and backend != "none":
            return None
        return WorkflowPlan(
            scope=scope,
            backend=backend,
            route=route,
            reason=reason,
            used_router="external",
            seed_sources=[str(s) for s in seeds],
        )

    @staticmethod
    def _request_features(request: Dict[str, Any]) -> Dict[str, Any]:
        seed_volume = request.get("seed_volume")
        return {
            "has_bbox": bool(request.get("bbox")),
            "has_memory_bbox": bool(request.get("memory_bbox")),
            "has_seed_volume": isinstance(seed_volume, np.ndarray) and seed_volume.ndim == 3 and bool(np.any(seed_volume > 0)),
            "use_langsam_seeds": bool(request.get("use_langsam_seeds")),
            "seed_mode": request.get("seed_mode", ""),
            "volume_shape": list(request.get("volume_shape", [])),
        }

    def _heuristic_plan(self, scope: str, request: Dict[str, Any], available: Dict[str, Dict[str, Any]]) -> WorkflowPlan:
        prompt = str(request.get("prompt", "") or "").lower()
        has_bbox = bool(request.get("bbox"))
        has_memory_bbox = bool(request.get("memory_bbox"))
        seed_volume = request.get("seed_volume")
        has_seed_volume = isinstance(seed_volume, np.ndarray) and seed_volume.ndim == 3 and bool(np.any(seed_volume > 0))
        is_cell_task = bool(request.get("cell_task")) or any(token in prompt for token in self.CELL_PROMPT_TOKENS)
        seed_sources = []
        if has_seed_volume:
            seed_sources.append("manual")
        if has_memory_bbox:
            seed_sources.append("memory")
        if bool(request.get("use_langsam_seeds")):
            seed_sources.append("langsam")
        if has_bbox:
            seed_sources.append("bbox")

        if scope == "volume":
            if is_cell_task and available.get("CellSeg", {}).get("ok", False):
                return WorkflowPlan(scope, "CellSeg", "slice_wise_cellseg", "cell microscopy prompt detected; using built-in CellSeg per slice", seed_sources=seed_sources)
            if available.get("MedSAM2", {}).get("ok", False):
                reason = "volume request; MedSAM2 selected for 3D propagation"
                route = "hybrid_text_memory_seeded_3d" if seed_sources else "text_to_3d"
                return WorkflowPlan(scope, "MedSAM2", route, reason, seed_sources=seed_sources)
            if available.get("MedSAM", {}).get("ok", False):
                return WorkflowPlan(scope, "MedSAM", "slice_wise_medsam", "MedSAM2 unavailable; falling back to 2D prompt propagation", seed_sources=seed_sources)
            if available.get("LangSAM", {}).get("ok", False):
                return WorkflowPlan(scope, "LangSAM", "slice_wise_langsam", "MedSAM2/MedSAM unavailable; using text masks per slice", seed_sources=seed_sources)
            return WorkflowPlan(scope, "none", "unavailable", "no configured segmentation backend", seed_sources=seed_sources)

        if is_cell_task and available.get("CellSeg", {}).get("ok", False):
            return WorkflowPlan(scope, "CellSeg", "microscopy_cell_instances", "cell microscopy prompt detected; CellSeg selected", seed_sources=seed_sources)
        if has_bbox or has_memory_bbox:
            if available.get("MedSAM", {}).get("ok", False):
                return WorkflowPlan(scope, "MedSAM", "bbox_to_2d_mask", "bbox prompt available; MedSAM selected", seed_sources=seed_sources)
            if available.get("MedSAM2", {}).get("ok", False):
                return WorkflowPlan(scope, "MedSAM2", "bbox_to_single_slice_3d", "bbox prompt available; MedSAM2 single-slice fallback", seed_sources=seed_sources)
        if available.get("LangSAM", {}).get("ok", False):
            return WorkflowPlan(scope, "LangSAM", "text_to_2d_mask", "no bbox prompt; LangSAM selected from language prompt", seed_sources=seed_sources)
        if available.get("MedSAM2", {}).get("ok", False):
            return WorkflowPlan(scope, "MedSAM2", "single_slice_3d", "LangSAM unavailable; MedSAM2 single-slice fallback", seed_sources=seed_sources)
        if available.get("MedSAM", {}).get("ok", False):
            return WorkflowPlan(scope, "MedSAM", "unprompted_2d_fallback", "LangSAM/MedSAM2 unavailable; MedSAM bridge fallback", seed_sources=seed_sources)
        return WorkflowPlan(scope, "none", "unavailable", "no configured segmentation backend", seed_sources=seed_sources)


class AgenticWorkflowAgent(BaseSegmentationAgent):
    name = "AgenticWorkflow"

    def __init__(self):
        self.agents: Dict[str, BaseSegmentationAgent] = {
            "CellSeg": CellSegAgent(),
            "LangSAM": LangSAMAgent(),
            "MedSAM": MedSAMAgent(),
            "MedSAM2": MedSAM2Agent(),
        }
        self.router = AgenticTaskRouter()
        self.last_routing: Dict[str, Any] = {}
        self.last_route_explanation: str = ""

    def is_available(self) -> Tuple[bool, str]:
        details = []
        ready = []
        for name, agent in self.agents.items():
            ok, detail = agent.is_available()
            details.append(f"{name}: {'ready' if ok else 'not ready'} ({detail})")
            if ok:
                ready.append(name)
        router = "external router configured" if os.environ.get("AGENT_ROUTER_CMD", "").strip() else "heuristic router"
        if ready:
            return True, f"{router}; available backends: {', '.join(ready)}. " + " | ".join(details)
        return False, f"{router}; no segmentation backend is ready. " + " | ".join(details)

    def supports_volume(self) -> bool:
        return True

    def predict(self, image_gray_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentResult:
        req: Dict[str, Any] = dict(request or {})
        if req.get("memory_bbox") and not req.get("bbox"):
            req["bbox"] = req["memory_bbox"]
        plan = self.router.plan("slice", prompt, req, self.agents)
        self._set_last_routing(plan, "slice", prompt, req)
        if plan.backend == "none":
            return AgentResult([], f"AgenticWorkflow: {plan.message()}", routing=self.last_routing)
        agent = self.agents.get(plan.backend)
        if agent is None:
            return AgentResult([], f"AgenticWorkflow: invalid routed backend {plan.backend}", routing=self.last_routing)
        start = time.perf_counter()
        result = agent.predict(image_gray_u8, prompt, request=req)
        message = f"AgenticWorkflow {plan.message()} | {result.message} | total={_elapsed_ms(start):.1f} ms"
        self._set_last_routing(plan, "slice", prompt, req, backend_message=result.message)
        return AgentResult(result.masks, message, routing=self.last_routing)

    def predict_volume(self, volume_u8: np.ndarray, prompt: str, request: Optional[dict] = None) -> AgentVolumeResult:
        req: Dict[str, Any] = dict(request or {})
        req["volume_shape"] = list(volume_u8.shape)
        if req.get("memory_bbox") and not req.get("bbox"):
            req["bbox"] = req["memory_bbox"]
        plan = self.router.plan("volume", prompt, req, self.agents)
        self._set_last_routing(plan, "volume", prompt, req)
        start = time.perf_counter()
        if plan.backend == "none":
            return AgentVolumeResult(None, f"AgenticWorkflow: {plan.message()}", routing=self.last_routing)
        if plan.backend == "MedSAM2":
            if req.get("use_langsam_seeds"):
                seed_vol, seed_msg = self._build_langsam_seed_volume(volume_u8, prompt, req)
                if seed_vol is not None:
                    existing = req.get("seed_volume")
                    req["seed_volume"] = np.maximum(existing, seed_vol) if isinstance(existing, np.ndarray) else seed_vol
                    plan.seed_sources = sorted(set((plan.seed_sources or []) + ["langsam"]))
                    req["langsam_seed_message"] = seed_msg
            result = self.agents["MedSAM2"].predict_volume(volume_u8, prompt, request=req)
            msg = f"AgenticWorkflow {plan.message()} | {result.message} | total={_elapsed_ms(start):.1f} ms"
            if req.get("langsam_seed_message"):
                msg += f" | {req['langsam_seed_message']}"
            self._set_last_routing(plan, "volume", prompt, req, backend_message=result.message)
            return AgentVolumeResult(result.mask_volume, msg, routing=self.last_routing)

        mask_volume, message = self._predict_volume_slice_wise(volume_u8, prompt, req, plan)
        self._set_last_routing(plan, "volume", prompt, req, backend_message=message)
        return AgentVolumeResult(mask_volume, f"AgenticWorkflow {plan.message()} | {message} | total={_elapsed_ms(start):.1f} ms", routing=self.last_routing)

    def explain_last_routing(self) -> Tuple[str, Dict[str, Any]]:
        return self.last_route_explanation, dict(self.last_routing)

    def _set_last_routing(
        self,
        plan: WorkflowPlan,
        scope: str,
        prompt: str,
        request: Dict[str, Any],
        *,
        backend_message: str = "",
    ) -> None:
        available = self.router._available_agents(self.agents)
        routing = plan.to_routing_dict(available)
        prompt_lower = (prompt or "").lower()
        routing["prompt_interpretation"] = {
            "text_prompt": prompt or "",
            "has_text": bool((prompt or "").strip()),
            "is_cell_task": any(token in prompt_lower for token in AgenticTaskRouter.CELL_PROMPT_TOKENS),
        }
        routing["image_type_guess"] = "medical_volume" if scope == "volume" else "unknown_2d"
        routing["request_features"] = self.router._request_features(request)
        routing["backend_message"] = backend_message
        self.last_routing = routing
        lines = [
            f"Selected backend: {routing.get('selected_backend')}",
            f"Reason: {routing.get('decision_reason')}",
            f"Route: {routing.get('route')}",
            f"Ranked candidates: {', '.join(routing.get('ranked_candidates', []))}",
        ]
        unavailable = routing.get("unavailable_backends") or {}
        if unavailable:
            lines.append("Unavailable: " + "; ".join(f"{k}: {v}" for k, v in unavailable.items()))
        if backend_message:
            lines.append(f"Backend message: {backend_message}")
        self.last_route_explanation = "\n".join(lines)

    def _build_langsam_seed_volume(self, volume_u8: np.ndarray, prompt: str, request: Dict[str, Any]) -> Tuple[Optional[np.ndarray], str]:
        langsam = self.agents.get("LangSAM")
        if langzaam is None:
            return None, "LangSAM seed builder unavailable."
        ok, detail = langzaam.is_available()
        if not ok:
            return None, detail
        stride = max(1, int(request.get("langsam_seed_stride", 5)))
        z_count, h, w = volume_u8.shape
        seed = np.zeros((z_count, h, w), dtype=np.uint8)
        count = 0
        for z in range(0, z_count, stride):
            result = langzaam.predict(volume_u8[z], prompt, request={"seed_role": "langsam_text_seed"})
            merged = np.zeros((h, w), dtype=np.uint8)
            for mask in result.masks:
                if mask is not None and mask.shape == (h, w):
                    merged = np.maximum(merged, (mask > 0).astype(np.uint8))
            if np.any(merged):
                seed[z] = merged
                count += 1
        if count <= 0:
            return None, f"LangSAM generated 0 text seed slice(s), stride={stride}."
        return seed, f"LangSAM generated {count} text seed slice(s), stride={stride}."

    def _predict_volume_slice_wise(
        self,
        volume_u8: np.ndarray,
        prompt: str,
        request: Dict[str, Any],
        plan: WorkflowPlan,
    ) -> Tuple[Optional[np.ndarray], str]:
        agent = self.agents.get(plan.backend)
        if agent is None:
            return None, f"invalid routed backend {plan.backend}"
        z_count, h, w = volume_u8.shape
        out = np.zeros((z_count, h, w), dtype=np.uint8)
        count = 0
        last_msg = ""
        seed_volume = request.get("seed_volume")
        for z in range(z_count):
            per_slice_request = dict(request)
            if isinstance(seed_volume, np.ndarray) and seed_volume.shape == volume_u8.shape and np.any(seed_volume[z] > 0):
                bbox = _mask_to_bbox(seed_volume[z])
                if bbox is not None:
                    per_slice_request["bbox"] = bbox
            result = agent.predict(volume_u8[z], prompt, request=per_slice_request)
            if result.message:
                last_msg = result.message
            merged = np.zeros((h, w), dtype=np.uint8)
            for mask in result.masks:
                if mask is not None and mask.shape == (h, w):
                    merged = np.maximum(merged, (mask > 0).astype(np.uint8))
            if np.any(merged):
                out[z] = merged
                count += 1
        return out, f"slice-wise fallback produced masks on {count}/{z_count} slice(s). {last_msg}"


def _mask_to_bbox(mask: np.ndarray) -> Optional[List[int]]:
    ys, xs = np.where(mask > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def build_agent_registry() -> Dict[str, BaseSegmentationAgent]:
    agents: Dict[str, BaseSegmentationAgent] = {}
    for cls in (AgenticWorkflowAgent, CellSegAgent, LangSAMAgent, MedSAMAgent, MedSAM2Agent):
        inst = cls()
        agents[inst.name] = inst
    return agents
