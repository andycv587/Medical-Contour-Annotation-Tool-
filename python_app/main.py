import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
import uuid
from tkinter import filedialog, ttk, messagebox, colorchooser, simpledialog

import cv2
import nibabel as nib
import numpy as np
from PIL import Image, ImageSequence, ImageTk
from PIL import ImageDraw

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ai_agents import build_agent_registry
from agent_memory import AgenticMemory, compute_volume_signature
from contour_io.exporters import (
    export_coco_json,
    export_nifti_mask,
    export_png_mask,
    export_polygon_json,
    export_tiff_stack,
)
from provenance.gui_logger import GuiEventLogger
from provenance.schema import file_hash


class ContourAnnotationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Contour Annotation Tool (Python)")
        self.root.geometry("1200x760")

        self.volume = None
        self.volume_raw = None
        self.loaded_nifti = None
        self.slice_axis = 0
        self.mask = None
        self.slice_index = 0
        self.window_min = 0.0
        self.window_max = 1.0
        self.raw_min = 0.0
        self.raw_max = 1.0
        self.opacity = 0.2
        self.threshold = 0.5
        self._image_tk = None
        self.annotation_mode = False
        self.current_polygon = []
        self.annotation_hint = tk.StringVar(value="Annotate: OFF")
        self.mask_label_var = tk.StringVar(value="Default")
        self.mask_color_var = tk.StringVar(value="#ff0000")
        self.mask_layer_var = tk.StringVar(value="Layer 1")
        self.view_layer_var = tk.StringVar(value="All")
        self.label_color_map = {"Default": "#ff0000"}
        self.watershed_fg_ratio = tk.DoubleVar(value=0.35)
        self.watershed_open_iters = tk.IntVar(value=1)
        self.watershed_bg_dilate_iters = tk.IntVar(value=2)
        self.levelset_iterations = tk.IntVar(value=20)
        self.levelset_kernel_size = tk.IntVar(value=3)
        self.segmentation_min_area = tk.IntVar(value=20)
        self.show_committed_overlays = tk.BooleanVar(value=True)
        self.show_preview_overlays = tk.BooleanVar(value=False)
        self.overlays_by_slice = {}
        self.masks_by_slice = {}
        self.preview_overlays_by_slice = {}
        self.preview_masks_by_slice = {}
        self.selected_overlay_index_by_slice = {}
        self.selected_preview_index_by_slice = {}
        self.ai_agents = build_agent_registry()
        self.ai_agent_name = tk.StringVar(value="MedSAM2")
        self.ai_prompt = tk.StringVar(value="bbox/seed")
        self.langsam_cmd = tk.StringVar(value=os.environ.get("LANGSAM_INFER_CMD", self.default_bridge_cmd("langsam_bridge_stub.py")))
        self.medsam_cmd = tk.StringVar(value=os.environ.get("MEDSAM_INFER_CMD", self.default_bridge_cmd("medsam_bridge_stub.py")))
        self.medsam2_cmd = tk.StringVar(value=os.environ.get("MEDSAM2_INFER_CMD", self.default_bridge_cmd("medsam2_bridge_stub.py")))
        self.agent_router_cmd = tk.StringVar(value=os.environ.get("AGENT_ROUTER_CMD", ""))
        self.ai_use_drawn_prompt = tk.BooleanVar(value=False)
        self.ai_use_3d_seed_prompt = tk.BooleanVar(value=True)
        self.ai_use_langsam_text_seed = tk.BooleanVar(value=False)
        self.ai_use_memory = tk.BooleanVar(value=False)
        self.ai_persist_memory = tk.BooleanVar(value=False)
        self.ai_langsam_stride = tk.IntVar(value=5)
        self.ai_seed_labels_var = tk.StringVar(value="All")
        self.ai_status = tk.StringVar(value="AI: idle")
        self.ai_memory_status = tk.StringVar(value="Memory: idle")
        self.ai_route_status = tk.StringVar(value="Route: no routing decision yet")
        self.ai_progress_status = tk.StringVar(value="Progress: idle")
        self.ai_progress_var = tk.DoubleVar(value=0.0)
        self.ai_busy = False
        self.ai_memory = AgenticMemory()
        self.current_volume_signature = ""
        self.current_image_hash = None
        self.session_id = f"gui-{uuid.uuid4().hex[:12]}"
        self.project_id = self.session_id
        self.gui_logger = GuiEventLogger(session_id=self.session_id, project_id=self.project_id)
        self.gui_log_path_var = tk.StringVar(value=f"Session log: {self.gui_logger.session_path}")
        self.last_routing_decision = {}
        self.last_route_explanation = ""
        self.gui_click_count = 0
        self.gui_prompt_count = 0
        self.gui_correction_count = 0
        self.gui_accepted_preview_count = 0
        self.gui_rejected_preview_count = 0
        self.undo_stack = []
        self.redo_stack = []
        self._view_origin_x = 0
        self._view_origin_y = 0
        self._view_width = 1
        self._view_height = 1

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)
        self.log_gui_event("app_start")

    @staticmethod
    def default_bridge_cmd(script_name: str) -> str:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
        return subprocess.list2cmdline([sys.executable, script_path])

    def current_image_metadata(self) -> dict:
        path = self.nifti_path_var.get().strip() if hasattr(self, "nifti_path_var") else ""
        shape = list(self.volume.shape) if self.volume is not None else []
        return {
            "image_filename": path or None,
            "image_hash": self.current_image_hash,
            "image_shape": shape,
            "active_slice": int(self.slice_index) if self.volume is not None else None,
        }

    def log_gui_event(self, event_type: str, *, sidecar_path: str = "", **kwargs):
        try:
            data = self.current_image_metadata()
            data.update(kwargs)
            data.setdefault("selected_backend", self.ai_agent_name.get() if hasattr(self, "ai_agent_name") else None)
            data.setdefault("backend_name", data.get("selected_backend"))
            data.setdefault("prompt", self.ai_prompt.get() if hasattr(self, "ai_prompt") else None)
            data.setdefault("routing_decision", self.last_routing_decision)
            data.setdefault("route_explanation", self.last_route_explanation)
            data.setdefault("fallback_history", self.last_routing_decision.get("fallback_history", []) if self.last_routing_decision else [])
            data.setdefault("click_count", self.gui_click_count)
            data.setdefault("prompt_count", self.gui_prompt_count)
            data.setdefault("correction_count", self.gui_correction_count)
            data.setdefault("accepted_preview_count", self.gui_accepted_preview_count)
            data.setdefault("rejected_preview_count", self.gui_rejected_preview_count)
            event = self.gui_logger.log(event_type, sidecar_path=sidecar_path, **data)
            if self.gui_logger.session_path:
                self.gui_log_path_var.set(f"Session log: {self.gui_logger.session_path}")
            return event
        except Exception:
            return {}

    def update_route_explanation(self, routing: dict, *, backend_message: str = ""):
        if not isinstance(routing, dict):
            return
        self.last_routing_decision = dict(routing)
        selected = routing.get("selected_backend", "unknown")
        ranked = routing.get("ranked_candidates") or []
        unavailable = routing.get("unavailable_backends") or {}
        fallbacks = routing.get("fallback_history") or []
        warnings = []
        mode = self.backend_mode_label(selected)
        if unavailable:
            warnings.append(f"{len(unavailable)} backend(s) unavailable")
        lines = [
            f"Selected: {selected} ({mode})",
            f"Reason: {routing.get('decision_reason', '')}",
            f"Ranked: {', '.join(str(x) for x in ranked)}",
        ]
        if unavailable:
            lines.append("Unavailable: " + "; ".join(f"{k}: {v}" for k, v in unavailable.items()))
        if fallbacks:
            lines.append("Fallbacks: " + "; ".join(f"{x.get('backend')}={x.get('status')}" for x in fallbacks))
        if backend_message:
            lines.append(f"Backend: {backend_message}")
        if warnings:
            lines.append("Warnings: " + "; ".join(warnings))
        self.last_route_explanation = "\n".join(lines)
        self.ai_route_status.set(self.last_route_explanation)

    def backend_mode_label(self, backend_name: str) -> str:
        name = (backend_name or "").lower()
        if name in {"mock"}:
            return "mock"
        if name in {"classical", "cellseg"}:
            return "lightweight/classical"
        env_map = {
            "langsam": "LANGSAM_INFER_CMD",
            "medsam": "MEDSAM_INFER_CMD",
            "medsam2": "MEDSAM2_INFER_CMD",
        }
        env_name = env_map.get(name)
        if env_name:
            cmd = os.environ.get(env_name, "").lower()
            if "bridge_stub.py" in cmd:
                return "stub external bridge"
            if cmd:
                return "external command"
            return "direct import or NOT_CONFIGURED"
        return "unknown"

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Use an explicit paned layout so left panel cannot swallow the viewer area.
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bd=0)
        main_pane.grid(row=0, column=0, sticky="nsew")

        left = tk.Frame(main_pane, width=320)
        right = tk.Frame(main_pane, bg="black")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        main_pane.add(left, minsize=280, stretch="never")
        main_pane.add(right, minsize=420, stretch="always")
        self.main_pane = main_pane
        self.root.after(50, self._set_default_split_ratio)

        # Scrollable left control column
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        left_canvas = tk.Canvas(left, highlightthickness=0, borderwidth=0)
        left_scroll = tk.Scrollbar(left, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_canvas.grid(row=0, column=0, sticky="nsew")
        left_scroll.grid(row=0, column=1, sticky="ns")
        left_content = tk.Frame(left_canvas)
        self.left_content_window = left_canvas.create_window((0, 0), window=left_content, anchor="nw")
        left_content.bind("<Configure>", self._on_left_content_configure)
        left_canvas.bind("<Configure>", self._on_left_canvas_configure)
        left_canvas.bind("<MouseWheel>", self._on_left_mousewheel)
        left_content.bind("<MouseWheel>", self._on_left_mousewheel)
        self.left_canvas = left_canvas
        self.left_content = left_content
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel, add="+")

        # File controls
        file_box = tk.LabelFrame(left_content, text="Files", padx=8, pady=8)
        file_box.pack(fill="x", padx=6, pady=6)
        self.nifti_path_var = tk.StringVar()
        self.mask_path_var = tk.StringVar()
        tk.Entry(file_box, textvariable=self.nifti_path_var).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        tk.Button(file_box, text="Choose Volume/Image", command=self.choose_nifti).grid(row=0, column=1)
        tk.Entry(file_box, textvariable=self.mask_path_var).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(6, 0))
        tk.Button(file_box, text="Choose Masks", command=self.choose_mask).grid(row=1, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export PNG Masks", command=self.export_png_masks).grid(row=2, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export NIfTI Mask", command=self.export_nifti_mask).grid(row=3, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export TIFF Stack", command=self.export_tiff_stack_mask).grid(row=4, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export Polygon JSON", command=self.export_polygon_json_file).grid(row=5, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export COCO JSON", command=self.export_coco_json_file).grid(row=6, column=1, pady=(6, 0))
        tk.Label(file_box, textvariable=self.gui_log_path_var, anchor="w", wraplength=260, justify="left").grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )
        file_box.columnconfigure(0, weight=1)

        # View controls
        tools_box = tk.LabelFrame(left_content, text="Tools", padx=8, pady=8)
        tools_box.pack(fill="x", padx=6, pady=6)

        threshold_group = tk.Frame(tools_box)
        threshold_group.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Label(threshold_group, text="Threshold").pack(side="left")
        self.threshold_value = tk.Label(threshold_group, text="0.000")
        self.threshold_value.pack(side="right")
        self.threshold_scale = tk.Scale(
            threshold_group, from_=0, to=1000, orient="horizontal", command=self.on_threshold_change, showvalue=False
        )
        self.threshold_scale.set(0)
        self.threshold_scale.pack(fill="x")
        self.bind_scale_mousewheel(self.threshold_scale)

        win_min_group = tk.Frame(tools_box)
        win_min_group.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        tk.Label(win_min_group, text="Window/Level Min").pack(side="left")
        self.win_min_value = tk.Label(win_min_group, text="0")
        self.win_min_value.pack(side="right")
        self.win_min_scale = tk.Scale(
            win_min_group, from_=0, to=1000, orient="horizontal", command=self.on_window_change, showvalue=False
        )
        self.win_min_scale.pack(fill="x")
        self.bind_scale_mousewheel(self.win_min_scale)

        win_max_group = tk.Frame(tools_box)
        win_max_group.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        tk.Label(win_max_group, text="Window/Level Max").pack(side="left")
        self.win_max_value = tk.Label(win_max_group, text="1")
        self.win_max_value.pack(side="right")
        self.win_max_scale = tk.Scale(
            win_max_group, from_=0, to=1000, orient="horizontal", command=self.on_window_change, showvalue=False
        )
        self.win_max_scale.set(1000)
        self.win_max_scale.pack(fill="x")
        self.bind_scale_mousewheel(self.win_max_scale)

        opacity_group = tk.Frame(tools_box)
        opacity_group.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        tk.Label(opacity_group, text="Opaque").pack(side="left")
        self.opacity_value = tk.Label(opacity_group, text="20")
        self.opacity_value.pack(side="right")
        self.opacity_scale = tk.Scale(
            opacity_group, from_=0, to=100, orient="horizontal", command=self.on_opacity_change, showvalue=False
        )
        self.opacity_scale.set(20)
        self.opacity_scale.pack(fill="x")
        self.bind_scale_mousewheel(self.opacity_scale)

        visibility_group = tk.Frame(tools_box)
        visibility_group.grid(row=4, column=0, sticky="ew")
        tk.Checkbutton(
            visibility_group,
            text="Show Committed",
            variable=self.show_committed_overlays,
            command=self.render_current_slice
        ).pack(side="left")
        tk.Checkbutton(
            visibility_group,
            text="Show Preview",
            variable=self.show_preview_overlays,
            command=self.render_current_slice
        ).pack(side="left", padx=(16, 0))
        tools_box.columnconfigure(0, weight=1)

        # Slice controls
        nav = tk.Frame(left_content)
        nav.pack(fill="x", padx=6, pady=(0, 6))
        tk.Button(nav, text="Prev Slice", command=lambda: self.move_slice(-1)).pack(side="left")
        tk.Button(nav, text="Next Slice", command=lambda: self.move_slice(1)).pack(side="left", padx=6)
        self.slice_label = tk.Label(nav, text="Slice: -/-")
        self.slice_label.pack(side="left", padx=8)
        self.shape_label = tk.Label(nav, text="Shape: -")
        self.shape_label.pack(side="left", padx=8)
        self.stats_label = tk.Label(nav, text="Stats: Cmt 0 | Prev 0")
        self.stats_label.pack(side="left", padx=8)

        # Action tabs
        tabs = ttk.Notebook(left_content)
        tabs.pack(fill="both", expand=True, padx=6, pady=6)
        ann = tk.Frame(tabs)
        wt = tk.Frame(tabs)
        lv = tk.Frame(tabs)
        ai = tk.Frame(tabs)
        tabs.add(ann, text="Annote")
        tabs.add(wt, text="Watershed")
        tabs.add(lv, text="Levelset")
        tabs.add(ai, text="AI Agent")
        ann_actions = tk.Frame(ann)
        ann_actions.pack(fill="x", padx=6, pady=(8, 4))
        self.annotation_button = tk.Button(ann_actions, text="Start Annotation", command=self.toggle_annotation_mode)
        self.annotation_button.pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Finish Polygon", command=self.finish_current_polygon).pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Cancel Polygon", command=self.cancel_current_polygon).pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Undo", command=self.undo).pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Redo", command=self.redo).pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Active Incision Mode").pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Clear Selected Overlay", command=self.clear_selected_overlay).pack(fill="x", padx=6, pady=2)
        tk.Button(ann_actions, text="Delete Selected Overlay/Mask", command=self.delete_selected_overlay_and_mask).pack(fill="x", padx=6, pady=2)

        ann_row2 = tk.Frame(ann)
        ann_row2.pack(fill="x", padx=12, pady=(0, 6))
        tk.Label(
            ann_row2,
            textvariable=self.annotation_hint,
            anchor="w",
            justify="left",
        ).pack(fill="x")
        ann_meta = tk.LabelFrame(ann, text="Mask Metadata", padx=6, pady=6)
        ann_meta.pack(fill="x", padx=6, pady=(0, 6))
        tk.Label(ann_meta, text="Label").grid(row=0, column=0, sticky="w")
        tk.Entry(ann_meta, textvariable=self.mask_label_var).grid(row=0, column=1, sticky="ew")
        tk.Label(ann_meta, text="Color").grid(row=1, column=0, sticky="w")
        tk.Entry(ann_meta, textvariable=self.mask_color_var).grid(row=1, column=1, sticky="ew")
        tk.Button(ann_meta, text="Pick Color", command=self.pick_mask_color).grid(row=1, column=2, padx=(6, 0), sticky="ew")
        tk.Label(ann_meta, text="Layer").grid(row=2, column=0, sticky="w")
        tk.Entry(ann_meta, textvariable=self.mask_layer_var).grid(row=2, column=1, sticky="ew")
        tk.Label(ann_meta, text="View Layer").grid(row=3, column=0, sticky="w")
        self.view_layer_combo = ttk.Combobox(ann_meta, textvariable=self.view_layer_var, values=["All", "Layer 1"], state="readonly")
        self.view_layer_combo.grid(row=3, column=1, sticky="ew")
        self.view_layer_combo.bind("<<ComboboxSelected>>", lambda _e: self.render_current_slice())
        tk.Button(ann_meta, text="Apply To Selected", command=self.apply_metadata_to_selected_overlay).grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(6, 0)
        )
        ann_meta.columnconfigure(1, weight=1)
        wt_actions = tk.LabelFrame(wt, text="Watershed Actions", padx=6, pady=6)
        wt_actions.pack(fill="x", padx=6, pady=(8, 4))
        tk.Button(wt_actions, text="Preview Current", command=self.preview_watershed_current).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Preview All", command=self.preview_watershed_all).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Apply Current", command=self.apply_watershed_current).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Apply All", command=self.apply_watershed_all).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Accept Preview", command=self.accept_preview_current).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Accept All Preview", command=self.accept_preview_all).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Reject Preview", command=self.reject_preview_current).pack(fill="x", pady=2)
        tk.Button(wt_actions, text="Reject All Preview", command=self.reject_preview_all).pack(fill="x", pady=2)

        wt_params = tk.LabelFrame(wt, text="Watershed Params", padx=8, pady=6)
        wt_params.pack(fill="x", padx=6, pady=(0, 8))
        tk.Label(wt_params, text="FG Ratio").grid(row=0, column=0, sticky="w")
        tk.Spinbox(wt_params, from_=0.05, to=0.95, increment=0.05, format="%.2f", textvariable=self.watershed_fg_ratio, width=10).grid(row=0, column=1, sticky="ew")
        tk.Label(wt_params, text="Open Iters").grid(row=1, column=0, sticky="w")
        tk.Spinbox(wt_params, from_=0, to=10, textvariable=self.watershed_open_iters, width=10).grid(row=1, column=1, sticky="ew")
        tk.Label(wt_params, text="BG Dilate Iters").grid(row=2, column=0, sticky="w")
        tk.Spinbox(wt_params, from_=1, to=20, textvariable=self.watershed_bg_dilate_iters, width=10).grid(row=2, column=1, sticky="ew")
        tk.Label(wt_params, text="Min Area").grid(row=3, column=0, sticky="w")
        tk.Spinbox(wt_params, from_=1, to=5000, textvariable=self.segmentation_min_area, width=10).grid(row=3, column=1, sticky="ew")
        wt_params.columnconfigure(1, weight=1)

        lv_actions = tk.LabelFrame(lv, text="Levelset Actions", padx=6, pady=6)
        lv_actions.pack(fill="x", padx=6, pady=(8, 4))
        tk.Button(lv_actions, text="Preview Current", command=self.preview_levelset_current).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Preview All", command=self.preview_levelset_all).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Apply Current", command=self.apply_levelset_current).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Apply All", command=self.apply_levelset_all).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Accept Preview", command=self.accept_preview_current).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Accept All Preview", command=self.accept_preview_all).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Reject Preview", command=self.reject_preview_current).pack(fill="x", pady=2)
        tk.Button(lv_actions, text="Reject All Preview", command=self.reject_preview_all).pack(fill="x", pady=2)

        lv_params = tk.LabelFrame(lv, text="Levelset Params", padx=8, pady=6)
        lv_params.pack(fill="x", padx=6, pady=(0, 8))
        tk.Label(lv_params, text="Iterations").grid(row=0, column=0, sticky="w")
        tk.Spinbox(lv_params, from_=1, to=200, textvariable=self.levelset_iterations, width=10).grid(row=0, column=1, sticky="ew")
        tk.Label(lv_params, text="Smooth Kernel").grid(row=1, column=0, sticky="w")
        tk.Spinbox(lv_params, from_=1, to=15, increment=2, textvariable=self.levelset_kernel_size, width=10).grid(row=1, column=1, sticky="ew")
        tk.Label(lv_params, text="Min Area").grid(row=2, column=0, sticky="w")
        tk.Spinbox(lv_params, from_=1, to=5000, textvariable=self.segmentation_min_area, width=10).grid(row=2, column=1, sticky="ew")
        lv_params.columnconfigure(1, weight=1)

        ai_form = tk.LabelFrame(ai, text="AI Backend", padx=6, pady=6)
        ai_form.pack(fill="x", padx=6, pady=(8, 4))
        tk.Label(ai_form, text="Backend").grid(row=0, column=0, sticky="w")
        ai_backend_combo = ttk.Combobox(
            ai_form,
            textvariable=self.ai_agent_name,
            values=["MedSAM2"],
            width=12,
            state="readonly",
        )
        ai_backend_combo.grid(row=0, column=1, sticky="ew")
        ai_backend_combo.bind("<<ComboboxSelected>>", self.on_ai_backend_changed)
        tk.Label(ai_form, text="MedSAM2 Cmd").grid(row=1, column=0, sticky="w")
        tk.Entry(ai_form, textvariable=self.medsam2_cmd).grid(row=1, column=1, sticky="ew")
        tk.Label(ai_form, text="Seed Labels").grid(row=2, column=0, sticky="w")
        tk.Entry(ai_form, textvariable=self.ai_seed_labels_var).grid(row=2, column=1, sticky="ew")
        tk.Label(ai_form, text="(comma-separated, or All)", anchor="w").grid(row=3, column=0, columnspan=2, sticky="w")
        tk.Button(ai_form, text="Check MedSAM2", command=self.check_ai_backend).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ai_form.columnconfigure(1, weight=1)

        ai_actions = tk.LabelFrame(ai, text="AI Actions", padx=6, pady=6)
        ai_actions.pack(fill="x", padx=6, pady=(0, 4))
        tk.Button(ai_actions, text="Preview Current", command=self.preview_ai_current).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Preview All", command=self.preview_ai_all).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Accept Current", command=self.accept_preview_current).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Accept All", command=self.accept_preview_all).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Reject Current", command=self.reject_preview_current).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Reject All", command=self.reject_preview_all).pack(fill="x", pady=2)

        ai_status_row = tk.Frame(ai)
        ai_status_row.pack(fill="x", padx=6, pady=(0, 8))
        tk.Label(ai_status_row, textvariable=self.ai_status, anchor="w").pack(fill="x")
        tk.Label(ai_status_row, textvariable=self.ai_progress_status, anchor="w").pack(fill="x")
        self.ai_progress_bar = ttk.Progressbar(
            ai_status_row,
            variable=self.ai_progress_var,
            maximum=100,
            mode="determinate",
        )
        self.ai_progress_bar.pack(fill="x", pady=(3, 0))

        self.ai_agent_name.set("MedSAM2")

        # Image viewport
        self.canvas = tk.Canvas(right, bg="black", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _e: self.render_current_slice())
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-1>", self.on_canvas_left_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<Double-Button-1>", lambda _e: self.finish_current_polygon())
        self.root.bind("<Return>", lambda _e: self.finish_current_polygon())
        self.root.bind("<Escape>", lambda _e: self.cancel_current_polygon())

    def _set_default_split_ratio(self):
        if not hasattr(self, "main_pane"):
            return
        total_w = max(1, self.root.winfo_width())
        x = int(total_w * 0.25)
        try:
            self.main_pane.sash_place(0, x, 1)
        except Exception:
            pass

    def _on_left_content_configure(self, _event):
        if hasattr(self, "left_canvas"):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _on_left_canvas_configure(self, event):
        if hasattr(self, "left_content_window"):
            self.left_canvas.itemconfigure(self.left_content_window, width=event.width)

    def _on_left_mousewheel(self, event):
        if not hasattr(self, "left_canvas"):
            return
        delta = int(event.delta / 120) if event.delta else 0
        if delta != 0:
            self.left_canvas.yview_scroll(-delta, "units")

    def _on_global_mousewheel(self, event):
        # Scroll left control pane when pointer is anywhere inside it.
        if not hasattr(self, "left_canvas"):
            return
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            return
        if self._is_descendant_of_left_panel(widget):
            self._on_left_mousewheel(event)

    def _is_descendant_of_left_panel(self, widget):
        current = widget
        while current is not None:
            if current == self.left_canvas or current == self.left_content:
                return True
            parent_name = current.winfo_parent()
            if not parent_name:
                break
            try:
                current = current.nametowidget(parent_name)
            except Exception:
                break
        return False

    @staticmethod
    def bind_scale_mousewheel(scale_widget: tk.Scale):
        def _on_scale_wheel(event):
            delta = int(event.delta / 120) if event.delta else 0
            if delta == 0:
                return "break"
            cur = int(float(scale_widget.get()))
            lo = int(float(scale_widget.cget("from")))
            hi = int(float(scale_widget.cget("to")))
            nxt = cur + (1 if delta > 0 else -1)
            nxt = max(min(lo, hi), min(max(lo, hi), nxt))
            scale_widget.set(nxt)
            return "break"

        scale_widget.bind("<MouseWheel>", _on_scale_wheel)

    @staticmethod
    def load_image_volume(path: str) -> np.ndarray:
        frames = []
        with Image.open(path) as img:
            for frame in ImageSequence.Iterator(img):
                if frame.mode in ("RGB", "RGBA", "P", "CMYK"):
                    arr = np.asarray(frame.convert("L"), dtype=np.float32)
                else:
                    arr = np.asarray(frame)
                    arr = np.squeeze(arr)
                    if arr.ndim == 3:
                        arr = np.asarray(Image.fromarray(arr).convert("L"), dtype=np.float32)
                    elif arr.ndim != 2:
                        raise ValueError(f"Unsupported image frame shape: {arr.shape}")
                    arr = arr.astype(np.float32)
                frames.append(arr)
        if not frames:
            raise ValueError("Image file did not contain readable frames.")
        first_shape = frames[0].shape
        if any(frame.shape != first_shape for frame in frames):
            raise ValueError("All image frames/pages must have the same shape.")
        return np.stack(frames, axis=0).astype(np.float32)

    def choose_nifti(self):
        path = filedialog.askopenfilename(
            title="Choose Volume or Image",
            filetypes=[
                ("NIfTI / Images", "*.nii *.nii.gz *.png *.jpg *.jpeg *.tif *.tiff *.bmp"),
                ("NIfTI", "*.nii *.nii.gz"),
                ("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        try:
            lower_path = path.lower()
            if lower_path.endswith(".nii") or lower_path.endswith(".nii.gz"):
                nii = nib.load(path)
                data = np.asarray(nii.get_fdata(dtype=np.float32))
                data = np.squeeze(data)
                if data.ndim != 3:
                    raise ValueError(f"Only 3D NIfTI volumes are supported right now, got shape={data.shape}")

                # Put likely slice axis first (usually the smallest dimension count).
                slice_axis = int(np.argmin(np.array(data.shape)))
                data = np.moveaxis(data, slice_axis, 0)
            else:
                nii = None
                slice_axis = 0
                data = self.load_image_volume(path)

            self.loaded_nifti = nii
            self.slice_axis = slice_axis
            self.volume_raw = data.copy()
            self.volume = data
            self.slice_index = 0
            self.raw_min = float(np.min(data))
            self.raw_max = float(np.max(data))
            if self.raw_max <= self.raw_min:
                self.raw_max = self.raw_min + 1.0
            self.window_min = self.raw_min
            self.window_max = self.raw_max
            self.overlays_by_slice = {}
            self.masks_by_slice = {}
            self.preview_overlays_by_slice = {}
            self.preview_masks_by_slice = {}
            self.selected_overlay_index_by_slice = {}
            self.selected_preview_index_by_slice = {}
            self.current_polygon = []
            self.set_annotation_mode(False)
            self.mask_layer_var.set("Layer 1")
            self.view_layer_var.set("All")
            self.undo_stack = []
            self.redo_stack = []
            self.nifti_path_var.set(path)
            self.current_volume_signature = compute_volume_signature(self.volume, path)
            self.current_image_hash = file_hash(path)
            self.ai_memory_status.set(f"Memory: volume {self.current_volume_signature}")
            self.shape_label.config(text=f"Shape: {tuple(self.volume.shape)}")
            self.win_min_scale.set(0)
            self.win_max_scale.set(1000)
            self.threshold_scale.set(0)
            self.update_window_labels()
            self.refresh_layer_options()
            self.render_current_slice()
            self.log_gui_event("image_loaded", parameters={"slice_axis": int(self.slice_axis), "source_path": path})
        except Exception as ex:
            self.log_gui_event("image_loaded", errors=[str(ex)], parameters={"source_path": path})
            messagebox.showerror("Load Error", str(ex))

    def choose_mask(self):
        path = filedialog.askopenfilename(
            title="Choose Mask",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All files", "*.*")]
        )
        if not path:
            return
        self.mask_path_var.set(path)

    def export_png_masks(self):
        if self.volume is None:
            messagebox.showwarning("Export", "Load NIfTI first.")
            return
        if not self.confirm_export_with_summary("PNG Masks"):
            return
        out_dir = filedialog.askdirectory(title="Choose folder for PNG masks")
        if not out_dir:
            return
        vol_mask = self.build_mask_volume_oriented()
        count = 0
        for z in range(vol_mask.shape[0]):
            arr = (vol_mask[z] > 0).astype(np.uint8)
            if np.any(arr):
                out_path = os.path.join(out_dir, f"mask_{z:04d}.png")
                export_png_mask(arr, out_path)
                self.log_gui_event(
                    "export_mask",
                    sidecar_path=self.gui_logger.sidecar_path_for_output(out_path),
                    export_action="png",
                    output_path=out_path,
                    active_slice=int(z),
                    parameters={"export_format": "PNG", "nonzero": int(np.count_nonzero(arr))},
                )
                count += 1
        messagebox.showinfo("Export", f"Exported {count} PNG mask slice(s).")

    def export_nifti_mask(self):
        if self.volume is None or self.loaded_nifti is None:
            messagebox.showwarning("Export", "Load NIfTI first.")
            return
        if not self.confirm_export_with_summary("NIfTI Mask"):
            return
        out_path = filedialog.asksaveasfilename(
            title="Save NIfTI mask",
            defaultextension=".nii.gz",
            filetypes=[("NIfTI GZip", "*.nii.gz"), ("NIfTI", "*.nii"), ("All files", "*.*")]
        )
        if not out_path:
            return
        vol_mask = self.build_mask_volume_oriented()
        restored = np.moveaxis(vol_mask, 0, self.slice_axis)
        export_nifti_mask(restored, out_path, affine=self.loaded_nifti.affine, header=self.loaded_nifti.header)
        self.log_gui_event(
            "export_mask",
            sidecar_path=self.gui_logger.sidecar_path_for_output(out_path),
            export_action="nifti",
            output_path=out_path,
            parameters={"export_format": "NIfTI", "nonzero": int(np.count_nonzero(restored))},
        )
        messagebox.showinfo("Export", f"Saved NIfTI mask:\n{out_path}")

    def export_tiff_stack_mask(self):
        if self.volume is None:
            messagebox.showwarning("Export", "Load volume/image first.")
            return
        if not self.confirm_export_with_summary("TIFF Stack"):
            return
        out_path = filedialog.asksaveasfilename(
            title="Save TIFF stack mask",
            defaultextension=".tif",
            filetypes=[("TIFF", "*.tif *.tiff"), ("All files", "*.*")],
        )
        if not out_path:
            return
        vol_mask = self.build_mask_volume_oriented()
        try:
            export_tiff_stack(vol_mask, out_path)
            self.log_gui_event(
                "export_mask",
                sidecar_path=self.gui_logger.sidecar_path_for_output(out_path),
                export_action="tiff_stack",
                output_path=out_path,
                parameters={"export_format": "TIFF stack", "nonzero": int(np.count_nonzero(vol_mask))},
            )
            messagebox.showinfo("Export", f"Saved TIFF stack mask:\n{out_path}")
        except Exception as ex:
            self.log_gui_event("export_mask", export_action="tiff_stack", output_path=out_path, errors=[str(ex)])
            messagebox.showwarning("Export", f"TIFF stack export failed:\n{ex}")

    def export_polygon_json_file(self):
        if self.volume is None:
            messagebox.showwarning("Export", "Load volume/image first.")
            return
        if not self.confirm_export_with_summary("Polygon JSON"):
            return
        out_path = filedialog.asksaveasfilename(
            title="Save polygon JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not out_path:
            return
        try:
            polygons_by_slice = self.polygons_payload_by_slice()
            metadata = {
                "project_id": self.project_id,
                "session_id": self.session_id,
                "image_filename": self.nifti_path_var.get().strip(),
                "image_shape": list(self.volume.shape),
                "preview_exported": False,
            }
            export_polygon_json(polygons_by_slice, out_path, metadata=metadata)
            self.log_gui_event(
                "export_mask",
                sidecar_path=self.gui_logger.sidecar_path_for_output(out_path),
                export_action="polygon_json",
                output_path=out_path,
                parameters={"export_format": "polygon JSON", "slice_count": len(polygons_by_slice)},
            )
            self.log_gui_event("export_project", output_path=out_path, export_action="polygon_json")
            messagebox.showinfo("Export", f"Saved polygon JSON:\n{out_path}")
        except Exception as ex:
            self.log_gui_event("export_mask", export_action="polygon_json", output_path=out_path, errors=[str(ex)])
            messagebox.showwarning("Export", f"Polygon JSON export failed:\n{ex}")

    def export_coco_json_file(self):
        if self.volume is None:
            messagebox.showwarning("Export", "Load volume/image first.")
            return
        if not self.confirm_export_with_summary("COCO JSON"):
            return
        instance_mask = self.build_instance_mask_for_slice(self.slice_index)
        if instance_mask is None or not np.any(instance_mask):
            messagebox.showwarning("Export", "COCO export needs committed instance-like masks on the current slice.")
            self.log_gui_event(
                "export_mask",
                export_action="coco_json",
                warnings=["COCO export skipped: no current-slice committed masks"],
            )
            return
        out_path = filedialog.asksaveasfilename(
            title="Save COCO JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not out_path:
            return
        try:
            export_coco_json(instance_mask, out_path, image_id=int(self.slice_index) + 1, category_name=self.mask_label_var.get() or "object")
            self.log_gui_event(
                "export_mask",
                sidecar_path=self.gui_logger.sidecar_path_for_output(out_path),
                export_action="coco_json",
                output_path=out_path,
                parameters={
                    "export_format": "COCO JSON",
                    "slice_index": int(self.slice_index),
                    "instance_count": int(np.max(instance_mask)),
                },
            )
            messagebox.showinfo("Export", f"Saved COCO JSON for current slice:\n{out_path}")
        except Exception as ex:
            self.log_gui_event("export_mask", export_action="coco_json", output_path=out_path, errors=[str(ex)])
            messagebox.showwarning("Export", f"COCO JSON export failed:\n{ex}")

    def on_threshold_change(self, _):
        self.threshold = self.threshold_scale.get() / 1000.0
        self.threshold_value.config(text=f"{self.threshold:.3f}")
        self.render_current_slice()

    def on_window_change(self, _):
        if self.volume is None:
            return
        lo = min(self.win_min_scale.get(), self.win_max_scale.get() - 1)
        hi = max(self.win_max_scale.get(), lo + 1)
        self.win_min_scale.set(lo)
        self.win_max_scale.set(hi)
        span = self.raw_max - self.raw_min
        self.window_min = self.raw_min + (lo / 1000.0) * span
        self.window_max = self.raw_min + (hi / 1000.0) * span
        self.update_window_labels()
        self.render_current_slice()
        self.log_gui_event(
            "window_level_changed",
            parameters={"window_min": float(self.window_min), "window_max": float(self.window_max)},
        )

    def on_opacity_change(self, _):
        self.opacity = self.opacity_scale.get() / 100.0
        self.opacity_value.config(text=str(self.opacity_scale.get()))
        self.render_current_slice()

    def update_window_labels(self):
        self.win_min_value.config(text=f"{self.window_min:.3f}")
        self.win_max_value.config(text=f"{self.window_max:.3f}")

    def move_slice(self, delta: int):
        if self.volume is None:
            return
        before = self.slice_index
        self.slice_index = max(0, min(self.volume.shape[0] - 1, self.slice_index + delta))
        self.render_current_slice()
        if self.slice_index != before:
            self.log_gui_event("slice_changed", parameters={"previous_slice": int(before), "slice_delta": int(delta)})

    def on_mouse_wheel(self, event):
        self.move_slice(-1 if event.delta > 0 else 1)

    def render_current_slice(self):
        self.canvas.delete("all")
        if self.volume is None:
            self.update_stats_label()
            return
        z = self.slice_index
        img = self.volume[z]
        img = np.nan_to_num(img, nan=self.raw_min, posinf=self.raw_max, neginf=self.raw_min)
        wl = np.clip(img, self.window_min, self.window_max)
        denom = max(1e-6, self.window_max - self.window_min)
        norm = ((wl - self.window_min) / denom * 255.0).astype(np.uint8)

        # Optional threshold visualization overlay (very light behavior)
        if self.threshold > 0:
            t = int(self.threshold * 255)
            norm = np.where(norm > t, norm, norm // 2).astype(np.uint8)

        base_rgba = Image.fromarray(norm, mode="L").convert("RGBA")
        overlay_rgba = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_rgba, "RGBA")
        if self.show_committed_overlays.get():
            overlays = self.overlays_by_slice.get(z, [])
            selected_idx = self.selected_overlay_index_by_slice.get(z, -1)
            view_layer = self.get_active_view_layer()
            for idx, overlay in enumerate(overlays):
                if view_layer != "All" and overlay.get("layer", "Layer 1") != view_layer:
                    continue
                pts = overlay["points"]
                if len(pts) < 3:
                    continue
                r, g, b = self.hex_to_rgb(overlay.get("color", "#ff0000"))
                fill = (r, g, b, int(255 * self.opacity))
                outline = (r, g, b, 240 if idx == selected_idx else 220)
                draw.polygon(pts, fill=fill, outline=outline)
                if idx == selected_idx:
                    draw.line(pts + [pts[0]], fill=(255, 255, 0, 255), width=3)
        if self.show_preview_overlays.get():
            preview_overlays = self.preview_overlays_by_slice.get(z, [])
            selected_preview_idx = self.selected_preview_index_by_slice.get(z, -1)
            for idx, overlay in enumerate(preview_overlays):
                pts = overlay["points"]
                if len(pts) < 3:
                    continue
                draw.polygon(pts, fill=(0, 255, 255, int(255 * self.opacity)), outline=(0, 255, 255, 240))
                if idx == selected_preview_idx:
                    draw.line(pts + [pts[0]], fill=(255, 255, 0, 255), width=3)
        if self.annotation_mode and len(self.current_polygon) > 1:
            draw.line(self.current_polygon, fill=(0, 255, 255, 255), width=2)

        composed = Image.alpha_composite(base_rgba, overlay_rgba)

        c_w = max(1, self.canvas.winfo_width())
        c_h = max(1, self.canvas.winfo_height())
        scale = min(c_w / composed.width, c_h / composed.height)
        new_w = max(1, int(composed.width * scale))
        new_h = max(1, int(composed.height * scale))
        resized = composed.resize((new_w, new_h), Image.Resampling.BILINEAR)
        self._image_tk = ImageTk.PhotoImage(resized)
        x = (c_w - new_w) // 2
        y = (c_h - new_h) // 2
        self._view_origin_x = x
        self._view_origin_y = y
        self._view_width = new_w
        self._view_height = new_h
        self.canvas.create_image(x, y, anchor="nw", image=self._image_tk)
        self.slice_label.config(text=f"Slice: {z + 1}/{self.volume.shape[0]}")
        self.update_stats_label()

    def update_stats_label(self):
        if self.volume is None:
            self.stats_label.config(text="Stats: Cmt 0 | Prev 0")
            return
        stats = self.collect_overlay_stats()
        self.stats_label.config(
            text=(
                f"Stats: Cur Cmt {stats['current_committed']}, Cur Prev {stats['current_preview']} | "
                f"Slices Cmt {stats['committed_slice_count']}, Prev {stats['preview_slice_count']} | "
                f"Total Cmt {stats['total_committed']}, Prev {stats['total_preview']}"
            )
        )

    def collect_overlay_stats(self):
        z = self.slice_index
        return {
            "current_committed": len(self.overlays_by_slice.get(z, [])),
            "current_preview": len(self.preview_overlays_by_slice.get(z, [])),
            "preview_slice_count": sum(1 for v in self.preview_overlays_by_slice.values() if v),
            "committed_slice_count": sum(1 for v in self.overlays_by_slice.values() if v),
            "total_committed": sum(len(v) for v in self.overlays_by_slice.values()),
            "total_preview": sum(len(v) for v in self.preview_overlays_by_slice.values()),
        }

    @staticmethod
    def hex_to_rgb(hex_color: str):
        v = (hex_color or "#ff0000").strip()
        if not v.startswith("#") or len(v) != 7:
            v = "#ff0000"
        try:
            return int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16)
        except Exception:
            return 255, 0, 0

    @staticmethod
    def normalize_layer_name(name: str) -> str:
        text = (name or "").strip()
        return text if text else "Layer 1"

    def get_active_view_layer(self) -> str:
        view = (self.view_layer_var.get() or "All").strip()
        return view if view else "All"

    def refresh_layer_options(self):
        layers = {"Layer 1"}
        for overlay_list in self.overlays_by_slice.values():
            for overlay in overlay_list:
                layers.add(self.normalize_layer_name(overlay.get("layer", "Layer 1")))
        values = ["All"] + sorted(layers)
        self.view_layer_combo["values"] = values
        if self.view_layer_var.get() not in values:
            self.view_layer_var.set("All")

    def parse_seed_label_filter(self):
        raw = (self.ai_seed_labels_var.get() or "All").strip()
        if not raw or raw.lower() == "all":
            return None
        parts = [p.strip() for p in raw.split(",")]
        labels = {p for p in parts if p}
        return labels or None

    def pick_mask_color(self):
        selected = colorchooser.askcolor(color=self.mask_color_var.get(), title="Pick mask color")
        if selected and selected[1]:
            self.mask_color_var.set(selected[1])

    def overlay_template_metadata(self):
        label = (self.mask_label_var.get() or "Default").strip() or "Default"
        color = (self.mask_color_var.get() or "").strip()
        if not color:
            color = self.label_color_map.get(label, "#ff0000")
        if label not in self.label_color_map:
            self.label_color_map[label] = color
        layer = self.normalize_layer_name(self.mask_layer_var.get())
        return label, color, layer

    def apply_metadata_to_selected_overlay(self):
        if self.volume is None:
            return
        z = self.slice_index
        overlays = self.overlays_by_slice.get(z, [])
        if not overlays:
            return
        idx = self.selected_overlay_index_by_slice.get(z, -1)
        if idx < 0 or idx >= len(overlays):
            return
        selected = overlays[idx]
        before = {
            "label": selected.get("label", "Default"),
            "color": selected.get("color", "#ff0000"),
            "layer": selected.get("layer", "Layer 1"),
        }
        label, color, layer = self.overlay_template_metadata()

        def do():
            selected["label"] = label
            selected["color"] = color
            selected["layer"] = layer
            self.refresh_layer_options()

        def undo():
            selected["label"] = before["label"]
            selected["color"] = before["color"]
            selected["layer"] = before["layer"]
            self.refresh_layer_options()

        self.execute_command(do, undo)
        self.render_current_slice()

    def confirm_export_with_summary(self, export_name: str) -> bool:
        stats = self.collect_overlay_stats()
        if stats["total_committed"] <= 0:
            messagebox.showwarning("Export", "No committed overlays/masks to export.")
            return False
        lines = [
            f"Export target: {export_name}",
            f"Committed overlays: {stats['total_committed']} across {stats['committed_slice_count']} slice(s).",
            f"Preview overlays (NOT exported): {stats['total_preview']} across {stats['preview_slice_count']} slice(s).",
        ]
        if stats["total_preview"] > 0:
            lines.append("Warning: preview results are not exported until you accept them.")
        lines.append("")
        lines.append("Continue export?")
        return bool(messagebox.askyesno("Confirm Export", "\n".join(lines)))

    def get_selected_ai_agent(self):
        return self.ai_agents.get(self.ai_agent_name.get())

    def should_use_drawn_prompt_for_ai(self) -> bool:
        # MedSAM2 is bbox/seed-prompted in this app. If a current polygon or
        # committed mask exists on the active slice, use it automatically.
        if self.ai_agent_name.get() == "MedSAM2":
            return True
        if self.ai_agent_name.get() == "MedSAM" and not self.ai_use_3d_seed_prompt.get():
            return True
        return self.ai_use_drawn_prompt.get()

    def on_ai_backend_changed(self, _event=None):
        if self.ai_agent_name.get() == "MedSAM2":
            self.ai_use_3d_seed_prompt.set(True)
            self.ai_status.set("AI: MedSAM2 selected, 3D seed mode enabled.")
        elif self.ai_agent_name.get() == "AgenticWorkflow":
            self.ai_status.set("AI: AgenticWorkflow selected, router and memory enabled.")
        self.log_gui_event("backend_selected", selected_backend=self.ai_agent_name.get())

    def check_ai_backend(self):
        self._sync_ai_environment()
        agent = self.get_selected_ai_agent()
        if agent is None:
            self.ai_status.set("AI: invalid backend selected")
            messagebox.showwarning("AI Agent", "Invalid backend selected.")
            return
        ok, detail = agent.is_available()
        self.ai_status.set(f"AI: {agent.name} {'ready' if ok else 'not ready'}")
        title = "AI Agent Ready" if ok else "AI Agent Not Ready"
        messagebox.showinfo(title, f"{agent.name}: {detail}")

    def show_ai_memory_summary(self):
        summary = self.ai_memory.summary()
        self.ai_memory_status.set(f"Memory: {summary}")
        messagebox.showinfo("Agentic Memory", summary)

    def clear_ai_short_memory(self):
        self.ai_memory.clear_short_term()
        self.ai_memory_status.set("Memory: short-term cleared")

    def set_ai_progress(self, value: float = None, message: str = None, *, indeterminate: bool = False, busy: bool = None):
        if busy is not None:
            self.ai_busy = bool(busy)
            self.root.config(cursor="watch" if self.ai_busy else "")
        if hasattr(self, "ai_progress_bar"):
            mode = "indeterminate" if indeterminate else "determinate"
            self.ai_progress_bar.configure(mode=mode)
            if indeterminate:
                self.ai_progress_bar.start(12)
            else:
                self.ai_progress_bar.stop()
        if value is not None:
            self.ai_progress_var.set(max(0.0, min(100.0, float(value))))
        if message is not None:
            self.ai_progress_status.set(f"Progress: {message}")
        self.root.update_idletasks()

    def finish_ai_progress(self, message: str = "done", value: float = 100.0):
        self.set_ai_progress(value=value, message=message, indeterminate=False, busy=False)

    def ensure_ai_not_busy(self) -> bool:
        if self.ai_busy:
            messagebox.showinfo("AI Agent", "MedSAM2 is already running. Wait for the current job to finish.")
            return False
        return True

    def get_current_volume_signature(self) -> str:
        if self.current_volume_signature:
            return self.current_volume_signature
        if self.volume is None:
            return "no-volume"
        self.current_volume_signature = compute_volume_signature(self.volume, self.nifti_path_var.get())
        return self.current_volume_signature

    def build_ai_request_context(self, scope: str, z: int = None) -> dict:
        request_payload = {
            "scope": scope,
            "use_langsam_seeds": bool(self.ai_use_langsam_text_seed.get()),
            "langsam_seed_stride": max(1, int(self.ai_langsam_stride.get())),
        }
        if self.volume is not None:
            request_payload["volume_shape"] = list(self.volume.shape)
        if not self.ai_use_memory.get() or self.volume is None:
            return request_payload

        hit = self.ai_memory.suggest_bbox(
            self.get_current_volume_signature(),
            self.ai_prompt.get().strip(),
            slice_index=z,
            use_short_term=True,
            use_long_term=bool(self.ai_persist_memory.get()),
        )
        if hit and hit.get("bbox"):
            request_payload["memory_bbox"] = hit["bbox"]
            request_payload["memory_source"] = hit.get("source", "")
            request_payload["memory_backend"] = hit.get("backend", "")
            self.ai_memory_status.set(f"Memory: suggested bbox {hit['bbox']} from {hit.get('source', 'memory')}")
            self.log_gui_event(
                "memory_suggestion_shown",
                bbox=hit["bbox"],
                parameters={"memory_source": hit.get("source", ""), "memory_backend": hit.get("backend", "")},
            )
            self.log_gui_event(
                "memory_suggestion_accepted",
                bbox=hit["bbox"],
                parameters={"acceptance": "auto_used_because_agentic_memory_toggle_enabled"},
            )
        return request_payload

    def polygons_to_mask(self, polygons, image_shape):
        h, w = image_shape
        mask_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask_img)
        for poly in polygons or []:
            if len(poly) >= 3:
                draw.polygon(poly, fill=255)
        return np.array(mask_img, dtype=np.uint8)

    def record_ai_memory_result(
        self,
        *,
        scope: str,
        action: str,
        elapsed_ms: float,
        message: str = "",
        polygons=None,
        image_shape=None,
        z: int = None,
        mask_volume: np.ndarray = None,
        metadata: dict = None,
    ):
        if self.volume is None or not self.ai_use_memory.get():
            return
        mask = None
        if polygons is not None and image_shape is not None:
            mask = self.polygons_to_mask(polygons, image_shape)
            if not np.any(mask):
                mask = None
        if mask is None and mask_volume is None:
            return
        if mask_volume is not None and not np.any(mask_volume > 0):
            return
        record = self.ai_memory.record(
            self.get_current_volume_signature(),
            self.ai_prompt.get().strip(),
            self.ai_agent_name.get(),
            scope,
            action,
            slice_index=z,
            mask=mask,
            mask_volume=mask_volume,
            elapsed_ms=elapsed_ms,
            message=message,
            metadata=metadata or {},
            persist=bool(self.ai_persist_memory.get()),
        )
        source = "persisted" if self.ai_persist_memory.get() else "session"
        if record.bbox_3d:
            self.ai_memory_status.set(f"Memory: {source} 3D bbox {record.bbox_3d}, {record.mask_slices} slice(s)")
        else:
            self.ai_memory_status.set(f"Memory: {source} bbox {record.bbox}, {record.mask_voxels} px")

    def slice_to_uint8(self, z: int) -> np.ndarray:
        img = self.volume[z]
        img = np.nan_to_num(img, nan=self.raw_min, posinf=self.raw_max, neginf=self.raw_min)
        wl = np.clip(img, self.window_min, self.window_max)
        denom = max(1e-6, self.window_max - self.window_min)
        return ((wl - self.window_min) / denom * 255.0).astype(np.uint8)

    def compute_ai_polygons_for_slice(self, z: int, drawn_prompt_mask=None, request_data=None):
        self._sync_ai_environment()
        agent = self.get_selected_ai_agent()
        if agent is None:
            return [], self.volume[z].shape, "Invalid backend selected."
        ok, detail = agent.is_available()
        if not ok:
            return [], self.volume[z].shape, detail
        norm = self.slice_to_uint8(z)
        norm_for_agent = norm
        use_bbox_only = self.ai_agent_name.get() in ("MedSAM", "MedSAM2")
        if drawn_prompt_mask is not None and drawn_prompt_mask.shape == norm.shape and not use_bbox_only:
            norm_for_agent = np.where(drawn_prompt_mask > 0, norm, 0).astype(np.uint8)
        request_payload = dict(request_data or {})
        if drawn_prompt_mask is not None and drawn_prompt_mask.shape == norm.shape:
            bbox = self.mask_to_bbox(drawn_prompt_mask)
            if bbox is not None:
                request_payload["bbox"] = bbox
        elif request_payload.get("memory_bbox") and not request_payload.get("bbox"):
            request_payload["bbox"] = request_payload["memory_bbox"]
        result = agent.predict(norm_for_agent, self.ai_prompt.get().strip(), request=request_payload)
        routing = getattr(result, "routing", None) or getattr(agent, "last_routing", None)
        if isinstance(routing, dict) and routing:
            self.update_route_explanation(routing, backend_message=result.message)
            self.log_gui_event("routing_decision", routing_decision=routing, route_explanation=self.last_route_explanation)
            if routing.get("fallback_history"):
                self.log_gui_event("backend_fallback", routing_decision=routing, parameters={"fallback_history": routing.get("fallback_history")})
        polygons = []
        for mask in result.masks:
            if mask is None:
                continue
            if mask.shape != norm.shape:
                continue
            effective_mask = mask.astype(np.uint8)
            if drawn_prompt_mask is not None and drawn_prompt_mask.shape == effective_mask.shape and not use_bbox_only:
                effective_mask = ((effective_mask > 0) & (drawn_prompt_mask > 0)).astype(np.uint8)
            polys = self.mask_to_polygons(effective_mask, min_area=self.get_segmentation_min_area())
            polygons.extend(polys)
        return polygons, norm.shape, result.message

    def get_drawn_prompt_mask_for_current_slice(self):
        if self.volume is None:
            return None
        z = self.slice_index
        h, w = self.volume[z].shape
        mask_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask_img)

        if len(self.current_polygon) >= 3:
            draw.polygon(self.current_polygon, fill=255)
            return np.array(mask_img, dtype=np.uint8)

        overlays = self.overlays_by_slice.get(z, [])
        if overlays:
            idx = self.selected_overlay_index_by_slice.get(z, len(overlays) - 1)
            if idx < 0 or idx >= len(overlays):
                idx = len(overlays) - 1
            pts = overlays[idx].get("points", [])
            if len(pts) >= 3:
                draw.polygon(pts, fill=255)
                return np.array(mask_img, dtype=np.uint8)
        return None

    @staticmethod
    def mask_to_bbox(mask: np.ndarray):
        ys, xs = np.where(mask > 0)
        if ys.size == 0 or xs.size == 0:
            return None
        x1, x2 = int(xs.min()), int(xs.max())
        y1, y2 = int(ys.min()), int(ys.max())
        return [x1, y1, x2, y2]

    @staticmethod
    def bbox_to_mask(bbox, shape):
        h, w = shape
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1 = max(0, min(w - 1, x1))
        x2 = max(0, min(w - 1, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(0, min(h - 1, y2))
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        m = np.zeros((h, w), dtype=np.uint8)
        m[y1:y2 + 1, x1:x2 + 1] = 255
        return m

    def collect_seed_masks_by_slice(self):
        seeds = {}
        if self.volume is None:
            return seeds
        label_filter = self.parse_seed_label_filter()
        z_count, h, w = self.volume.shape
        for z in range(z_count):
            overlays = self.overlays_by_slice.get(z, [])
            masks = self.masks_by_slice.get(z, [])
            if not overlays or not masks:
                continue
            combined = np.zeros((h, w), dtype=np.uint8)
            for idx, overlay in enumerate(overlays):
                if idx >= len(masks):
                    continue
                if label_filter is not None and overlay.get("label", "Default") not in label_filter:
                    continue
                m = masks[idx]
                if m is None or m.shape != (h, w):
                    continue
                combined = np.maximum(combined, (m > 0).astype(np.uint8) * 255)
            if np.any(combined):
                seeds[z] = combined
        return seeds

    def seed_masks_to_volume(self, seed_masks):
        if self.volume is None:
            return None
        z_count, h, w = self.volume.shape
        vol = np.zeros((z_count, h, w), dtype=np.uint8)
        for z, m in seed_masks.items():
            if 0 <= z < z_count and m is not None and m.shape == (h, w):
                vol[z] = (m > 0).astype(np.uint8)
        return vol

    def collect_langsam_seed_masks_by_slice(self):
        seeds = {}
        if self.volume is None:
            return seeds, "No volume loaded."
        langsam = self.ai_agents.get("LangSAM")
        if langsam is None:
            return seeds, "LangSAM backend not registered."
        ok, detail = langsam.is_available()
        if not ok:
            return seeds, detail
        stride = max(1, int(self.ai_langsam_stride.get()))
        prompt = self.ai_prompt.get().strip()
        if not prompt:
            return seeds, "Prompt is empty."

        z_count = self.volume.shape[0]
        for z in range(0, z_count, stride):
            img_u8 = self.slice_to_uint8(z)
            result = langsam.predict(img_u8, prompt)
            merged = np.zeros_like(img_u8, dtype=np.uint8)
            for m in result.masks:
                if m is not None and m.shape == img_u8.shape:
                    merged = np.maximum(merged, (m > 0).astype(np.uint8) * 255)
            if np.any(merged):
                seeds[z] = merged
        return seeds, f"LangSAM generated seeds on {len(seeds)} slice(s), stride={stride}."

    def densify_seed_volume(self, seed_volume: np.ndarray):
        if self.volume is None or seed_volume is None:
            return seed_volume
        if seed_volume.ndim != 3:
            return seed_volume
        z_count, h, w = seed_volume.shape
        out = (seed_volume > 0).astype(np.uint8) * 255
        seed_idx = [i for i in range(z_count) if np.any(out[i] > 0)]
        if not seed_idx:
            return out

        # Fill missing slices by nearest/interpolated bbox envelope from seed slices.
        for z in range(z_count):
            if np.any(out[z] > 0):
                continue
            lower = None
            upper = None
            for s in seed_idx:
                if s < z:
                    lower = s
                elif s > z:
                    upper = s
                    break
            if lower is None and upper is None:
                continue
            if lower is None:
                box = self.mask_to_bbox(out[upper])
                if box is not None:
                    out[z] = self.bbox_to_mask(box, (h, w))
                continue
            if upper is None:
                box = self.mask_to_bbox(out[lower])
                if box is not None:
                    out[z] = self.bbox_to_mask(box, (h, w))
                continue
            box_l = self.mask_to_bbox(out[lower])
            box_u = self.mask_to_bbox(out[upper])
            if box_l is None and box_u is None:
                continue
            if box_l is None:
                out[z] = self.bbox_to_mask(box_u, (h, w))
                continue
            if box_u is None:
                out[z] = self.bbox_to_mask(box_l, (h, w))
                continue
            t = float(z - lower) / float(max(1, upper - lower))
            interp = [int(round(box_l[i] + (box_u[i] - box_l[i]) * t)) for i in range(4)]
            out[z] = self.bbox_to_mask(interp, (h, w))

        # Slight spatial smoothing between adjacent slices for stable 3D propagation.
        for z in range(1, z_count - 1):
            cur = out[z] > 0
            prev = out[z - 1] > 0
            nxt = out[z + 1] > 0
            fused = ((cur.astype(np.uint8) + prev.astype(np.uint8) + nxt.astype(np.uint8)) >= 2).astype(np.uint8) * 255
            if np.any(fused):
                out[z] = fused
        return out

    def build_3d_seed_prompt_mask_for_slice(self, z: int, seed_masks):
        if not seed_masks or self.volume is None:
            return None
        if z in seed_masks:
            return seed_masks[z]
        h, w = self.volume[z].shape
        seed_slices = sorted(seed_masks.keys())
        lower = None
        upper = None
        for s in seed_slices:
            if s < z:
                lower = s
            elif s > z:
                upper = s
                break
        if lower is None and upper is None:
            return None
        if lower is None:
            bbox = self.mask_to_bbox(seed_masks[upper])
            return self.bbox_to_mask(bbox, (h, w)) if bbox else None
        if upper is None:
            bbox = self.mask_to_bbox(seed_masks[lower])
            return self.bbox_to_mask(bbox, (h, w)) if bbox else None
        box_l = self.mask_to_bbox(seed_masks[lower])
        box_u = self.mask_to_bbox(seed_masks[upper])
        if box_l is None and box_u is None:
            return None
        if box_l is None:
            return self.bbox_to_mask(box_u, (h, w))
        if box_u is None:
            return self.bbox_to_mask(box_l, (h, w))
        t = float(z - lower) / float(max(1, upper - lower))
        interp = [
            int(round(box_l[i] + (box_u[i] - box_l[i]) * t))
            for i in range(4)
        ]
        return self.bbox_to_mask(interp, (h, w))

    def _sync_ai_environment(self):
        langsam_cmd = self.langsam_cmd.get().strip()
        if langsam_cmd:
            os.environ["LANGSAM_INFER_CMD"] = langsam_cmd
        elif "LANGSAM_INFER_CMD" in os.environ:
            del os.environ["LANGSAM_INFER_CMD"]

        medsam_cmd = self.medsam_cmd.get().strip()
        if medsam_cmd:
            os.environ["MEDSAM_INFER_CMD"] = medsam_cmd
        elif "MEDSAM_INFER_CMD" in os.environ:
            del os.environ["MEDSAM_INFER_CMD"]

        medsam2_cmd = self.medsam2_cmd.get().strip()
        if medsam2_cmd:
            os.environ["MEDSAM2_INFER_CMD"] = medsam2_cmd
        elif "MEDSAM2_INFER_CMD" in os.environ:
            del os.environ["MEDSAM2_INFER_CMD"]

        router_cmd = self.agent_router_cmd.get().strip()
        if router_cmd:
            os.environ["AGENT_ROUTER_CMD"] = router_cmd
        elif "AGENT_ROUTER_CMD" in os.environ:
            del os.environ["AGENT_ROUTER_CMD"]

    def volume_to_uint8(self) -> np.ndarray:
        if self.volume is None:
            return np.zeros((0, 0, 0), dtype=np.uint8)
        z_count = self.volume.shape[0]
        out = []
        for z in range(z_count):
            out.append(self.slice_to_uint8(z))
        return np.stack(out, axis=0).astype(np.uint8)

    def set_preview_from_mask_volume(self, mask_volume: np.ndarray):
        if self.volume is None:
            return 0
        if mask_volume.ndim != 3:
            return 0
        z_count = min(self.volume.shape[0], mask_volume.shape[0])
        preview_slices = []
        for z in range(z_count):
            mask = (mask_volume[z] > 0).astype(np.uint8)
            polys = self.mask_to_polygons(mask, min_area=self.get_segmentation_min_area())
            if polys:
                self.set_preview_for_slice(z, polys, mask.shape)
                preview_slices.append(z)
            else:
                self.clear_preview_for_slice(z)
        if preview_slices:
            self.show_preview_overlays.set(True)
            if self.slice_index not in preview_slices:
                self.slice_index = min(preview_slices, key=lambda idx: abs(idx - self.slice_index))
        return len(preview_slices)

    def add_committed_from_mask_volume(self, mask_volume: np.ndarray):
        if self.volume is None:
            return 0
        if mask_volume.ndim != 3:
            return 0
        z_count = min(self.volume.shape[0], mask_volume.shape[0])
        apply_count = 0
        for z in range(z_count):
            mask = (mask_volume[z] > 0).astype(np.uint8)
            polys = self.mask_to_polygons(mask, min_area=self.get_segmentation_min_area())
            if polys:
                self.add_polygons_to_slice(z, polys, mask.shape)
                apply_count += 1
        return apply_count

    def run_medsam2_volume_async(self, *, action: str, agent, vol_u8: np.ndarray, prompt: str, request_payload: dict, status_parts):
        label = "preview" if action == "preview" else "apply"
        self.set_ai_progress(20, f"running MedSAM2 3D {label}...", indeterminate=True, busy=True)

        def worker():
            start = time.perf_counter()
            try:
                vr = agent.predict_volume(vol_u8, prompt, request=request_payload)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                self.root.after(0, lambda: self.finish_medsam2_volume_job(action, vr, elapsed_ms, request_payload, status_parts))
            except Exception as ex:
                message = str(ex)
                self.root.after(0, lambda message=message: self.fail_medsam2_volume_job(message))

        threading.Thread(target=worker, daemon=True).start()

    def fail_medsam2_volume_job(self, message: str):
        self.ai_status.set(f"AI: MedSAM2 failed: {message}")
        self.finish_ai_progress("failed", value=0)
        messagebox.showwarning("AI Agent", f"MedSAM2 failed: {message}")

    def finish_medsam2_volume_job(self, action: str, vr, elapsed_ms: float, request_payload: dict, status_parts):
        routing = getattr(vr, "routing", None) or getattr(self.get_selected_ai_agent(), "last_routing", None)
        if isinstance(routing, dict) and routing:
            self.update_route_explanation(routing, backend_message=vr.message)
            self.log_gui_event("routing_decision", routing_decision=routing, route_explanation=self.last_route_explanation)
            if routing.get("fallback_history"):
                self.log_gui_event("backend_fallback", routing_decision=routing, parameters={"fallback_history": routing.get("fallback_history")})
        if vr.mask_volume is None:
            self.ai_status.set(f"AI: {vr.message}")
            self.finish_ai_progress("failed", value=0)
            messagebox.showwarning("AI Agent", vr.message)
            return

        self.set_ai_progress(85, "converting MedSAM2 mask to overlays...", indeterminate=False, busy=True)
        if action == "preview":
            slice_count = self.set_preview_from_mask_volume(vr.mask_volume)
            self.record_ai_memory_result(
                scope="volume",
                action="preview",
                elapsed_ms=elapsed_ms,
                message=vr.message,
                mask_volume=vr.mask_volume,
                metadata={"request": request_payload},
            )
            self.ai_status.set(f"AI: previewed 3D volume on {slice_count} slice(s) ({elapsed_ms:.1f} ms).")
            event_action = "preview"
        else:
            slice_count = self.add_committed_from_mask_volume(vr.mask_volume)
            self.record_ai_memory_result(
                scope="volume",
                action="apply",
                elapsed_ms=elapsed_ms,
                message=vr.message,
                mask_volume=vr.mask_volume,
                metadata={"request": request_payload},
            )
            self.ai_status.set(f"AI: applied 3D volume on {slice_count} slice(s) ({elapsed_ms:.1f} ms).")
            event_action = "apply"

        self.log_gui_event(
            "segmentation_preview_generated" if action == "preview" else "segmentation_preview_accepted",
            runtime_sec=elapsed_ms / 1000.0,
            parameters={
                "scope": "volume",
                "action": event_action,
                "request": request_payload,
                "nonzero": int(np.count_nonzero(vr.mask_volume)),
                "slice_count": int(slice_count),
            },
        )
        self.render_current_slice()
        self.finish_ai_progress(f"{event_action} ready on {slice_count} slice(s)", value=100)
        if vr.message:
            if status_parts:
                messagebox.showinfo("AI Agent", f"{vr.message}\n" + "\n".join(status_parts))
            else:
                messagebox.showinfo("AI Agent", vr.message)

    def preview_ai_current(self):
        if not self.ensure_ai_not_busy():
            return
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        z = self.slice_index
        self.gui_prompt_count += 1
        self.log_gui_event("segmentation_preview_requested", parameters={"scope": "slice", "backend": self.ai_agent_name.get()})
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        request_data = self.build_ai_request_context("slice", z=z)
        self.set_ai_progress(20, "running current-slice preview...", indeterminate=True, busy=True)
        start = time.perf_counter()
        polygons, image_shape, msg = self.compute_ai_polygons_for_slice(z, drawn_prompt_mask=prompt_mask, request_data=request_data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.finish_ai_progress("current-slice preview done", value=100)
        suffix = f" | memory={request_data.get('memory_source')}" if request_data.get("memory_source") else ""
        self.ai_status.set(f"AI: {msg or 'done'} ({elapsed_ms:.1f} ms){suffix}")
        self.log_gui_event(
            "segmentation_preview_generated",
            runtime_sec=elapsed_ms / 1000.0,
            parameters={"scope": "slice", "polygon_count": len(polygons), "request": request_data},
        )
        if not polygons:
            self.clear_preview_for_slice(z)
            self.render_current_slice()
            if msg:
                messagebox.showinfo("AI Agent", msg)
            return
        self.set_preview_for_slice(z, polygons, image_shape)
        self.record_ai_memory_result(
            scope="slice",
            action="preview",
            elapsed_ms=elapsed_ms,
            message=msg,
            polygons=polygons,
            image_shape=image_shape,
            z=z,
            metadata={"request": request_data},
        )
        self.render_current_slice()

    def preview_ai_all(self):
        if not self.ensure_ai_not_busy():
            return
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        self.gui_prompt_count += 1
        self.log_gui_event("segmentation_preview_requested", parameters={"scope": "volume", "backend": self.ai_agent_name.get()})
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        seed_masks = self.collect_seed_masks_by_slice()
        if not seed_masks and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Need a current slice box/seed or committed seed mask for MedSAM2.")
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            agent = self.get_selected_ai_agent()
            if agent is not None and self.ai_agent_name.get() in ("MedSAM2", "AgenticWorkflow") and agent.supports_volume():
                self.set_ai_progress(5, "preparing volume and prompt...", indeterminate=False, busy=True)
                vol_u8 = self.volume_to_uint8()
                request_payload = self.build_ai_request_context("volume", z=self.slice_index)
                request_payload["seed_mode"] = "3d"
                request_payload["crop_to_seed_bounds"] = False
                status_parts = []
                if request_payload.get("memory_source"):
                    status_parts.append(f"memory bbox: {request_payload.get('memory_source')}")
                if seed_masks:
                    manual_seed_vol = self.seed_masks_to_volume(seed_masks)
                    status_parts.append(f"manual seeds: {len(seed_masks)} slice(s)")
                    if manual_seed_vol is not None:
                        # MedSAM2 should receive sparse user prompts. Densifying a single
                        # seed slice into the whole volume can shift the effective key frame.
                        request_payload["seed_volume"] = manual_seed_vol
                anchor_mask = self.get_drawn_prompt_mask_for_current_slice()
                if anchor_mask is not None:
                    bbox = self.mask_to_bbox(anchor_mask)
                    if bbox is not None:
                        request_payload["bbox"] = bbox
                        request_payload["bbox_slice_index"] = int(self.slice_index)
                self.run_medsam2_volume_async(
                    action="preview",
                    agent=agent,
                    vol_u8=vol_u8,
                    prompt=self.ai_prompt.get().strip(),
                    request_payload=request_payload,
                    status_parts=status_parts,
                )
                return

            preview_count = 0
            last_msg = ""
            start_all = time.perf_counter()
            result_volume = np.zeros(self.volume.shape, dtype=np.uint8)
            request_context_base = self.build_ai_request_context("volume", z=self.slice_index)
            for z in range(self.volume.shape[0]):
                self.set_ai_progress((z / max(1, self.volume.shape[0])) * 100.0, f"processing slice {z + 1}/{self.volume.shape[0]}", indeterminate=False, busy=True)
                per_slice_prompt = self.build_3d_seed_prompt_mask_for_slice(z, seed_masks) if seed_masks else prompt_mask
                request_data = dict(request_context_base)
                request_data["seed_mode"] = "3d" if seed_masks else "2d"
                polygons, image_shape, msg = self.compute_ai_polygons_for_slice(
                    z, drawn_prompt_mask=per_slice_prompt, request_data=request_data
                )
                if msg:
                    last_msg = msg
                if polygons:
                    self.set_preview_for_slice(z, polygons, image_shape)
                    result_volume[z] = self.polygons_to_mask(polygons, image_shape)
                    preview_count += 1
                else:
                    self.clear_preview_for_slice(z)
            elapsed_ms = (time.perf_counter() - start_all) * 1000.0
            if preview_count:
                self.record_ai_memory_result(
                    scope="volume",
                    action="preview",
                    elapsed_ms=elapsed_ms,
                    message=last_msg,
                    mask_volume=result_volume,
                    metadata={"request": request_context_base},
                )
            self.ai_status.set(f"AI: previewed {preview_count} slice(s) ({elapsed_ms:.1f} ms).")
            self.finish_ai_progress(f"preview ready on {preview_count} slice(s)", value=100)
            self.log_gui_event(
                "segmentation_preview_generated",
                runtime_sec=elapsed_ms / 1000.0,
                parameters={"scope": "volume_slice_wise", "preview_count": int(preview_count), "request": request_context_base},
            )
            self.render_current_slice()
            if last_msg:
                messagebox.showinfo("AI Agent", f"Previewed {preview_count} slice(s).\n{last_msg}")
        finally:
            self.root.config(cursor="")

    def apply_ai_current(self):
        if not self.ensure_ai_not_busy():
            return
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        z = self.slice_index
        self.gui_prompt_count += 1
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        request_data = self.build_ai_request_context("slice", z=z)
        self.set_ai_progress(20, "running current-slice apply...", indeterminate=True, busy=True)
        start = time.perf_counter()
        polygons, image_shape, msg = self.compute_ai_polygons_for_slice(z, drawn_prompt_mask=prompt_mask, request_data=request_data)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.finish_ai_progress("current-slice apply done", value=100)
        suffix = f" | memory={request_data.get('memory_source')}" if request_data.get("memory_source") else ""
        self.ai_status.set(f"AI: {msg or 'done'} ({elapsed_ms:.1f} ms){suffix}")
        if polygons:
            self.add_polygons_to_slice(z, polygons, image_shape)
            self.record_ai_memory_result(
                scope="slice",
                action="apply",
                elapsed_ms=elapsed_ms,
                message=msg,
                polygons=polygons,
                image_shape=image_shape,
                z=z,
                metadata={"request": request_data},
            )
        self.render_current_slice()
        if msg:
            messagebox.showinfo("AI Agent", msg)

    def apply_ai_all(self):
        if not self.ensure_ai_not_busy():
            return
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        self.gui_prompt_count += 1
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        seed_masks = self.collect_seed_masks_by_slice()
        if not seed_masks and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Need a current slice box/seed or committed seed mask for MedSAM2.")
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            agent = self.get_selected_ai_agent()
            if agent is not None and self.ai_agent_name.get() in ("MedSAM2", "AgenticWorkflow") and agent.supports_volume():
                self.set_ai_progress(5, "preparing volume and prompt...", indeterminate=False, busy=True)
                vol_u8 = self.volume_to_uint8()
                request_payload = self.build_ai_request_context("volume", z=self.slice_index)
                request_payload["seed_mode"] = "3d"
                request_payload["crop_to_seed_bounds"] = False
                status_parts = []
                if request_payload.get("memory_source"):
                    status_parts.append(f"memory bbox: {request_payload.get('memory_source')}")
                if seed_masks:
                    manual_seed_vol = self.seed_masks_to_volume(seed_masks)
                    status_parts.append(f"manual seeds: {len(seed_masks)} slice(s)")
                    if manual_seed_vol is not None:
                        # MedSAM2 should receive sparse user prompts. Densifying a single
                        # seed slice into the whole volume can shift the effective key frame.
                        request_payload["seed_volume"] = manual_seed_vol
                anchor_mask = self.get_drawn_prompt_mask_for_current_slice()
                if anchor_mask is not None:
                    bbox = self.mask_to_bbox(anchor_mask)
                    if bbox is not None:
                        request_payload["bbox"] = bbox
                        request_payload["bbox_slice_index"] = int(self.slice_index)
                self.run_medsam2_volume_async(
                    action="apply",
                    agent=agent,
                    vol_u8=vol_u8,
                    prompt=self.ai_prompt.get().strip(),
                    request_payload=request_payload,
                    status_parts=status_parts,
                )
                return

            apply_count = 0
            last_msg = ""
            start_all = time.perf_counter()
            result_volume = np.zeros(self.volume.shape, dtype=np.uint8)
            request_context_base = self.build_ai_request_context("volume", z=self.slice_index)
            for z in range(self.volume.shape[0]):
                self.set_ai_progress((z / max(1, self.volume.shape[0])) * 100.0, f"processing slice {z + 1}/{self.volume.shape[0]}", indeterminate=False, busy=True)
                per_slice_prompt = self.build_3d_seed_prompt_mask_for_slice(z, seed_masks) if seed_masks else prompt_mask
                request_data = dict(request_context_base)
                request_data["seed_mode"] = "3d" if seed_masks else "2d"
                polygons, image_shape, msg = self.compute_ai_polygons_for_slice(
                    z, drawn_prompt_mask=per_slice_prompt, request_data=request_data
                )
                if msg:
                    last_msg = msg
                if polygons:
                    self.add_polygons_to_slice(z, polygons, image_shape)
                    result_volume[z] = self.polygons_to_mask(polygons, image_shape)
                    apply_count += 1
            elapsed_ms = (time.perf_counter() - start_all) * 1000.0
            if apply_count:
                self.record_ai_memory_result(
                    scope="volume",
                    action="apply",
                    elapsed_ms=elapsed_ms,
                    message=last_msg,
                    mask_volume=result_volume,
                    metadata={"request": request_context_base},
                )
            self.ai_status.set(f"AI: applied {apply_count} slice(s) ({elapsed_ms:.1f} ms).")
            self.finish_ai_progress(f"apply ready on {apply_count} slice(s)", value=100)
            self.render_current_slice()
            if last_msg:
                messagebox.showinfo("AI Agent", f"Applied on {apply_count} slice(s).\n{last_msg}")
        finally:
            self.root.config(cursor="")

    def apply_watershed_current(self):
        if self.volume is None:
            messagebox.showwarning("Watershed", "Load NIfTI first.")
            return
        z = self.slice_index
        polygons, image_shape = self.compute_watershed_polygons_for_slice(z)
        if polygons:
            self.add_polygons_to_slice(z, polygons, image_shape)
        self.render_current_slice()

    def apply_watershed_all(self):
        if self.volume is None:
            messagebox.showwarning("Watershed", "Load NIfTI first.")
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            for z in range(self.volume.shape[0]):
                polygons, image_shape = self.compute_watershed_polygons_for_slice(z)
                if polygons:
                    self.add_polygons_to_slice(z, polygons, image_shape)
            self.render_current_slice()
            messagebox.showinfo("Watershed", f"Applied to {self.volume.shape[0]} slice(s).")
        finally:
            self.root.config(cursor="")

    def preview_watershed_current(self):
        if self.volume is None:
            messagebox.showwarning("Watershed", "Load NIfTI first.")
            return
        z = self.slice_index
        self.log_gui_event("segmentation_preview_requested", selected_backend="watershed", parameters={"scope": "slice"})
        start = time.perf_counter()
        polygons, image_shape = self.compute_watershed_polygons_for_slice(z)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.log_gui_event(
            "segmentation_preview_generated",
            selected_backend="watershed",
            runtime_sec=elapsed_ms / 1000.0,
            parameters={"scope": "slice", "polygon_count": len(polygons)},
        )
        if not polygons:
            self.clear_preview_for_slice(z)
            self.render_current_slice()
            return
        self.set_preview_for_slice(z, polygons, image_shape)
        self.render_current_slice()

    def preview_watershed_all(self):
        if self.volume is None:
            messagebox.showwarning("Watershed", "Load NIfTI first.")
            return
        self.log_gui_event("segmentation_preview_requested", selected_backend="watershed", parameters={"scope": "volume"})
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            preview_count = 0
            start = time.perf_counter()
            for z in range(self.volume.shape[0]):
                polygons, image_shape = self.compute_watershed_polygons_for_slice(z)
                if polygons:
                    self.set_preview_for_slice(z, polygons, image_shape)
                    preview_count += 1
                else:
                    self.clear_preview_for_slice(z)
            self.render_current_slice()
            self.log_gui_event(
                "segmentation_preview_generated",
                selected_backend="watershed",
                runtime_sec=(time.perf_counter() - start),
                parameters={"scope": "volume", "preview_count": int(preview_count)},
            )
            messagebox.showinfo("Watershed", f"Previewed {preview_count} slice(s).")
        finally:
            self.root.config(cursor="")

    def compute_watershed_polygons_for_slice(self, z: int):
        img = self.volume[z]
        wl = np.clip(img, self.window_min, self.window_max)
        denom = max(1e-6, self.window_max - self.window_min)
        norm = ((wl - self.window_min) / denom * 255.0).astype(np.uint8)

        # Otsu foreground/background for marker construction
        _, thresh = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=self.get_watershed_open_iters())
        sure_bg = cv2.dilate(opening, kernel, iterations=self.get_watershed_bg_dilate_iters())
        dist = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist, self.get_watershed_fg_ratio() * dist.max(), 255, 0)
        sure_fg = sure_fg.astype(np.uint8)
        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        color = cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(color, markers)

        fg_mask = (markers > 1).astype(np.uint8)
        polygons = self.mask_to_polygons(fg_mask, min_area=self.get_segmentation_min_area())
        return polygons, fg_mask.shape

    def apply_levelset_current(self):
        if self.volume is None:
            messagebox.showwarning("Levelset", "Load NIfTI first.")
            return
        z = self.slice_index
        polygons, image_shape = self.compute_levelset_polygons_for_slice(z)
        if polygons:
            self.add_polygons_to_slice(z, polygons, image_shape)
        self.render_current_slice()

    def apply_levelset_all(self):
        if self.volume is None:
            messagebox.showwarning("Levelset", "Load NIfTI first.")
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            for z in range(self.volume.shape[0]):
                polygons, image_shape = self.compute_levelset_polygons_for_slice(z)
                if polygons:
                    self.add_polygons_to_slice(z, polygons, image_shape)
            self.render_current_slice()
            messagebox.showinfo("Levelset", f"Applied to {self.volume.shape[0]} slice(s).")
        finally:
            self.root.config(cursor="")

    def preview_levelset_current(self):
        if self.volume is None:
            messagebox.showwarning("Levelset", "Load NIfTI first.")
            return
        z = self.slice_index
        self.log_gui_event("segmentation_preview_requested", selected_backend="levelset", parameters={"scope": "slice"})
        start = time.perf_counter()
        polygons, image_shape = self.compute_levelset_polygons_for_slice(z)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.log_gui_event(
            "segmentation_preview_generated",
            selected_backend="levelset",
            runtime_sec=elapsed_ms / 1000.0,
            parameters={"scope": "slice", "polygon_count": len(polygons)},
        )
        if not polygons:
            self.clear_preview_for_slice(z)
            self.render_current_slice()
            return
        self.set_preview_for_slice(z, polygons, image_shape)
        self.render_current_slice()

    def preview_levelset_all(self):
        if self.volume is None:
            messagebox.showwarning("Levelset", "Load NIfTI first.")
            return
        self.log_gui_event("segmentation_preview_requested", selected_backend="levelset", parameters={"scope": "volume"})
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            preview_count = 0
            start = time.perf_counter()
            for z in range(self.volume.shape[0]):
                polygons, image_shape = self.compute_levelset_polygons_for_slice(z)
                if polygons:
                    self.set_preview_for_slice(z, polygons, image_shape)
                    preview_count += 1
                else:
                    self.clear_preview_for_slice(z)
            self.render_current_slice()
            self.log_gui_event(
                "segmentation_preview_generated",
                selected_backend="levelset",
                runtime_sec=(time.perf_counter() - start),
                parameters={"scope": "volume", "preview_count": int(preview_count)},
            )
            messagebox.showinfo("Levelset", f"Previewed {preview_count} slice(s).")
        finally:
            self.root.config(cursor="")

    def compute_levelset_polygons_for_slice(self, z: int):
        img = self.volume[z]
        img = np.nan_to_num(img, nan=self.raw_min, posinf=self.raw_max, neginf=self.raw_min)
        wl = np.clip(img, self.window_min, self.window_max)
        denom = max(1e-6, self.window_max - self.window_min)
        norm = ((wl - self.window_min) / denom * 255.0).astype(np.uint8)

        # Lightweight region-based active contour style iteration (levelset-like).
        f = cv2.GaussianBlur(norm, (5, 5), 0).astype(np.float32) / 255.0
        mask = f > float(np.mean(f))
        kernel_size = self.get_levelset_kernel_size()
        iterations = self.get_levelset_iterations()
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

        for _ in range(iterations):
            fg = f[mask]
            bg = f[~mask]
            if fg.size == 0 or bg.size == 0:
                break
            c1 = float(np.mean(fg))
            c0 = float(np.mean(bg))
            new_mask = (f - c1) ** 2 < (f - c0) ** 2
            m = (new_mask.astype(np.uint8) * 255)
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=1)
            mask = m > 0

        polygons = self.mask_to_polygons(mask.astype(np.uint8), min_area=self.get_segmentation_min_area())
        return polygons, mask.shape

    def set_preview_for_slice(self, z: int, polygons, image_shape):
        h, w = image_shape
        preview_overlays = []
        preview_masks = []
        label, color, layer = self.overlay_template_metadata()
        for poly in polygons:
            preview_overlays.append({"points": poly, "label": label, "color": color, "layer": layer})
            mask_img = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask_img).polygon(poly, fill=255)
            preview_masks.append(np.array(mask_img, dtype=np.uint8))
        self.preview_overlays_by_slice[z] = preview_overlays
        self.preview_masks_by_slice[z] = preview_masks
        self.show_preview_overlays.set(True)

    def clear_preview_for_slice(self, z: int):
        self.preview_overlays_by_slice.pop(z, None)
        self.preview_masks_by_slice.pop(z, None)
        self.selected_preview_index_by_slice.pop(z, None)

    def accept_preview_current(self):
        if self.volume is None:
            return
        z = self.slice_index
        preview_overlays_all = self.preview_overlays_by_slice.get(z, [])
        preview_masks_all = self.preview_masks_by_slice.get(z, [])
        selected_preview = self.selected_preview_index_by_slice.get(z, -1)
        if 0 <= selected_preview < len(preview_overlays_all):
            preview_overlays = [preview_overlays_all[selected_preview]]
            preview_masks = [preview_masks_all[selected_preview]] if selected_preview < len(preview_masks_all) else []
            accept_mode = "selected"
        else:
            preview_overlays = list(preview_overlays_all)
            preview_masks = list(preview_masks_all)
            accept_mode = "slice"
        if not preview_overlays:
            return
        overlays = self.overlays_by_slice.setdefault(z, [])
        masks = self.masks_by_slice.setdefault(z, [])
        selected_before = self.selected_overlay_index_by_slice.get(z, -1)
        preview_overlays_before = list(preview_overlays_all)
        preview_masks_before = list(preview_masks_all)
        selected_preview_before = selected_preview

        def do():
            overlays.extend(preview_overlays)
            masks.extend(preview_masks)
            self.selected_overlay_index_by_slice[z] = len(overlays) - 1
            if 0 <= selected_preview_before < len(self.preview_overlays_by_slice.get(z, [])):
                self.preview_overlays_by_slice[z].pop(selected_preview_before)
                if selected_preview_before < len(self.preview_masks_by_slice.get(z, [])):
                    self.preview_masks_by_slice[z].pop(selected_preview_before)
                self.selected_preview_index_by_slice[z] = -1
                if not self.preview_overlays_by_slice.get(z):
                    self.clear_preview_for_slice(z)
            else:
                self.clear_preview_for_slice(z)
            self.refresh_layer_options()

        def undo():
            remove_count = len(preview_overlays)
            if remove_count > 0 and len(overlays) >= remove_count:
                del overlays[-remove_count:]
            if remove_count > 0 and len(masks) >= remove_count:
                del masks[-remove_count:]
            self.selected_overlay_index_by_slice[z] = selected_before
            self.preview_overlays_by_slice[z] = list(preview_overlays_before)
            self.preview_masks_by_slice[z] = list(preview_masks_before)
            self.selected_preview_index_by_slice[z] = selected_preview_before
            self.refresh_layer_options()

        self.execute_command(do, undo)
        self.gui_accepted_preview_count += len(preview_overlays)
        self.log_gui_event(
            "segmentation_preview_accepted",
            parameters={"scope": "slice", "accept_mode": accept_mode, "accepted_overlay_count": len(preview_overlays)},
        )
        self.render_current_slice()

    def reject_preview_current(self):
        if self.volume is None:
            return
        z = self.slice_index
        preview_overlays = self.preview_overlays_by_slice.get(z, [])
        preview_masks = self.preview_masks_by_slice.get(z, [])
        selected_preview = self.selected_preview_index_by_slice.get(z, -1)
        if 0 <= selected_preview < len(preview_overlays):
            rejected = 1
            preview_overlays.pop(selected_preview)
            if selected_preview < len(preview_masks):
                preview_masks.pop(selected_preview)
            self.selected_preview_index_by_slice[z] = -1
            if not preview_overlays:
                self.clear_preview_for_slice(z)
            reject_mode = "selected"
        else:
            rejected = len(preview_overlays)
            self.clear_preview_for_slice(z)
            reject_mode = "slice"
        self.gui_rejected_preview_count += rejected
        self.log_gui_event(
            "segmentation_preview_rejected",
            parameters={"scope": "slice", "reject_mode": reject_mode, "rejected_overlay_count": int(rejected)},
        )
        self.render_current_slice()

    def accept_preview_all(self):
        if self.volume is None:
            return
        if not self.preview_overlays_by_slice:
            return

        preview_overlay_snapshot = {}
        preview_mask_snapshot = {}
        selected_before = {}
        slice_ids = sorted(self.preview_overlays_by_slice.keys())
        for z in slice_ids:
            preview_overlay_snapshot[z] = list(self.preview_overlays_by_slice.get(z, []))
            preview_mask_snapshot[z] = list(self.preview_masks_by_slice.get(z, []))
            selected_before[z] = self.selected_overlay_index_by_slice.get(z, -1)

        added_counts = {}

        def do():
            added_counts.clear()
            for z in slice_ids:
                overlays = self.overlays_by_slice.setdefault(z, [])
                masks = self.masks_by_slice.setdefault(z, [])
                add_overlays = preview_overlay_snapshot[z]
                add_masks = preview_mask_snapshot[z]
                overlays.extend(add_overlays)
                masks.extend(add_masks)
                added_counts[z] = len(add_overlays)
                self.selected_overlay_index_by_slice[z] = len(overlays) - 1 if overlays else -1
            self.preview_overlays_by_slice.clear()
            self.preview_masks_by_slice.clear()
            self.selected_preview_index_by_slice.clear()
            self.refresh_layer_options()

        def undo():
            for z in slice_ids:
                overlays = self.overlays_by_slice.get(z, [])
                masks = self.masks_by_slice.get(z, [])
                remove_count = added_counts.get(z, 0)
                if remove_count > 0 and len(overlays) >= remove_count:
                    del overlays[-remove_count:]
                if remove_count > 0 and len(masks) >= remove_count:
                    del masks[-remove_count:]
                self.selected_overlay_index_by_slice[z] = selected_before.get(z, -1)
                self.preview_overlays_by_slice[z] = list(preview_overlay_snapshot.get(z, []))
                self.preview_masks_by_slice[z] = list(preview_mask_snapshot.get(z, []))
                self.selected_preview_index_by_slice[z] = -1
            self.refresh_layer_options()

        self.execute_command(do, undo)
        accepted = sum(len(v) for v in preview_overlay_snapshot.values())
        self.gui_accepted_preview_count += accepted
        self.log_gui_event(
            "segmentation_preview_accepted",
            parameters={"scope": "volume", "accepted_overlay_count": int(accepted), "slice_count": len(slice_ids)},
        )
        self.render_current_slice()

    def reject_preview_all(self):
        if self.volume is None:
            return
        rejected = sum(len(v) for v in self.preview_overlays_by_slice.values())
        self.preview_overlays_by_slice.clear()
        self.preview_masks_by_slice.clear()
        self.selected_preview_index_by_slice.clear()
        self.gui_rejected_preview_count += rejected
        self.log_gui_event(
            "segmentation_preview_rejected",
            parameters={"scope": "volume", "rejected_overlay_count": int(rejected)},
        )
        self.render_current_slice()

    def add_polygons_to_slice(self, z: int, polygons, image_shape):
        overlays = self.overlays_by_slice.setdefault(z, [])
        masks = self.masks_by_slice.setdefault(z, [])
        h, w = image_shape
        label, color, layer = self.overlay_template_metadata()
        for poly in polygons:
            overlay = {"points": poly, "label": label, "color": color, "layer": layer}
            overlays.append(overlay)
            mask_img = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask_img).polygon(poly, fill=255)
            masks.append(np.array(mask_img, dtype=np.uint8))
        self.selected_overlay_index_by_slice[z] = len(overlays) - 1
        self.refresh_layer_options()

    @staticmethod
    def mask_to_polygons(mask: np.ndarray, min_area: int = 20):
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        polygons = []
        for c in contours:
            if len(c) < 3:
                continue
            area = cv2.contourArea(c)
            if area < float(min_area):
                continue
            poly = [(int(p[0][0]), int(p[0][1])) for p in c]
            polygons.append(poly)
        return polygons

    def get_levelset_iterations(self) -> int:
        value = int(self.levelset_iterations.get())
        return max(1, value)

    def get_watershed_fg_ratio(self) -> float:
        value = float(self.watershed_fg_ratio.get())
        return min(0.95, max(0.01, value))

    def get_watershed_open_iters(self) -> int:
        value = int(self.watershed_open_iters.get())
        return min(20, max(0, value))

    def get_watershed_bg_dilate_iters(self) -> int:
        value = int(self.watershed_bg_dilate_iters.get())
        return min(30, max(1, value))

    def get_levelset_kernel_size(self) -> int:
        value = int(self.levelset_kernel_size.get())
        value = max(1, value)
        if value % 2 == 0:
            value += 1
        return value

    def get_segmentation_min_area(self) -> int:
        value = int(self.segmentation_min_area.get())
        return max(1, value)

    def polygons_payload_by_slice(self):
        payload = {}
        for z, overlays in self.overlays_by_slice.items():
            records = []
            for overlay in overlays:
                points = [[int(x), int(y)] for x, y in overlay.get("points", [])]
                if len(points) < 3:
                    continue
                records.append(
                    {
                        "points": points,
                        "label": overlay.get("label", "Default"),
                        "color": overlay.get("color", "#ff0000"),
                        "layer": overlay.get("layer", "Layer 1"),
                    }
                )
            if records:
                payload[int(z)] = records
        return payload

    def build_instance_mask_for_slice(self, z: int):
        if self.volume is None:
            return None
        if z < 0 or z >= self.volume.shape[0]:
            return None
        h, w = self.volume[z].shape
        instance = np.zeros((h, w), dtype=np.uint16)
        value = 1
        for m in self.masks_by_slice.get(z, []):
            if m is None or m.shape != (h, w):
                continue
            binary = np.asarray(m) > 0
            if not np.any(binary):
                continue
            instance[binary] = value
            value += 1
        return instance

    def build_mask_volume_oriented(self):
        z_count, h, w = self.volume.shape
        vol_mask = np.zeros((z_count, h, w), dtype=np.uint8)
        for z, mask_list in self.masks_by_slice.items():
            if z < 0 or z >= z_count:
                continue
            for m in mask_list:
                if m is None:
                    continue
                if m.shape != (h, w):
                    continue
                vol_mask[z] = np.maximum(vol_mask[z], (m > 0).astype(np.uint8))
        return vol_mask

    def toggle_annotation_mode(self):
        was_enabled = self.annotation_mode
        had_polygon = bool(self.current_polygon)
        self.set_annotation_mode(not self.annotation_mode)
        if not self.annotation_mode:
            self.current_polygon = []
            if was_enabled and had_polygon:
                self.log_gui_event("manual_polygon_cancelled", parameters={"reason": "annotation_mode_toggled_off"})
        self.render_current_slice()

    def set_annotation_mode(self, enabled: bool):
        self.annotation_mode = bool(enabled)
        if self.annotation_mode:
            self.annotation_button.config(text="Stop Annotation")
            self.annotation_hint.set("Annotate: ON | Left click add points | Double-click / Enter / Right-click finish | Esc cancel")
            self.log_gui_event("manual_polygon_started")
        else:
            self.annotation_button.config(text="Start Annotation")
            self.annotation_hint.set("Annotate: OFF | Click Start Annotation to draw polygon")

    def on_canvas_left_click(self, event):
        image_pt = self.canvas_to_image_point(event.x, event.y)
        if image_pt is None or self.volume is None:
            return
        if self.annotation_mode:
            self.current_polygon.append(image_pt)
            self.gui_click_count += 1
            self.render_current_slice()
        else:
            self.select_overlay_at_point(image_pt)

    def on_canvas_right_click(self, event):
        if self.annotation_mode:
            _ = event
            self.finish_current_polygon()
            return
        image_pt = self.canvas_to_image_point(event.x, event.y)
        if image_pt is None or self.volume is None:
            return
        self.select_overlay_at_point(image_pt)
        z = self.slice_index
        preview_idx = self.selected_preview_index_by_slice.get(z, -1)
        preview_overlays = self.preview_overlays_by_slice.get(z, [])
        if 0 <= preview_idx < len(preview_overlays):
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Accept Selected Preview", command=self.accept_preview_current)
            menu.add_command(label="Reject Selected Preview", command=self.reject_preview_current)
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return
        idx = self.selected_overlay_index_by_slice.get(z, -1)
        overlays = self.overlays_by_slice.get(z, [])
        if idx < 0 or idx >= len(overlays):
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Delete Selected", command=self.delete_selected_overlay_only)
        menu.add_separator()
        menu.add_command(label="Set Label...", command=self.context_set_selected_label)
        menu.add_command(label="Set Color...", command=self.context_set_selected_color)
        menu.add_command(label="Set Layer...", command=self.context_set_selected_layer)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def finish_current_polygon(self):
        if not self.annotation_mode:
            return
        if len(self.current_polygon) < 3:
            self.annotation_hint.set("Annotate: need >= 3 points to finish polygon")
            self.render_current_slice()
            return
        self.commit_current_polygon()

    def canvas_to_image_point(self, cx, cy):
        if self.volume is None:
            return None
        if cx < self._view_origin_x or cy < self._view_origin_y:
            return None
        if cx >= self._view_origin_x + self._view_width or cy >= self._view_origin_y + self._view_height:
            return None
        rel_x = (cx - self._view_origin_x) / float(max(1, self._view_width))
        rel_y = (cy - self._view_origin_y) / float(max(1, self._view_height))
        img_h, img_w = self.volume[self.slice_index].shape
        ix = int(rel_x * img_w)
        iy = int(rel_y * img_h)
        ix = max(0, min(img_w - 1, ix))
        iy = max(0, min(img_h - 1, iy))
        return (ix, iy)

    def commit_current_polygon(self):
        z = self.slice_index
        polygon = list(self.current_polygon)
        self.current_polygon = []
        if len(polygon) < 3:
            self.render_current_slice()
            return
        # When user manually commits a polygon, keep this slice clean from preview overlays.
        self.clear_preview_for_slice(z)
        self.apply_add_overlay_command(z, polygon)
        self.annotation_hint.set("Annotate: polygon saved (continue drawing or stop annotation)")
        self.log_gui_event("manual_polygon_finished", points=[[int(x), int(y)] for x, y in polygon])
        self.render_current_slice()

    def apply_add_overlay_command(self, z, polygon):
        overlays = self.overlays_by_slice.setdefault(z, [])
        masks = self.masks_by_slice.setdefault(z, [])
        selected_before = self.selected_overlay_index_by_slice.get(z, -1)
        label, color, layer = self.overlay_template_metadata()

        img_h, img_w = self.volume[z].shape
        mask_img = Image.new("L", (img_w, img_h), 0)
        ImageDraw.Draw(mask_img).polygon(polygon, fill=255)
        mask_array = np.array(mask_img, dtype=np.uint8)

        overlay = {"points": polygon, "label": label, "color": color, "layer": layer}

        def do():
            overlays.append(overlay)
            masks.append(mask_array)
            self.selected_overlay_index_by_slice[z] = len(overlays) - 1
            self.refresh_layer_options()

        def undo():
            if overlays:
                overlays.pop()
            if masks:
                masks.pop()
            self.selected_overlay_index_by_slice[z] = selected_before
            self.refresh_layer_options()

        self.execute_command(do, undo)

    def select_overlay_at_point(self, image_pt):
        z = self.slice_index
        preview_overlays = self.preview_overlays_by_slice.get(z, [])
        selected_preview = -1
        if self.show_preview_overlays.get():
            for idx in range(len(preview_overlays) - 1, -1, -1):
                overlay = preview_overlays[idx]
                if self.point_in_polygon(image_pt, overlay["points"]):
                    selected_preview = idx
                    break
        if selected_preview >= 0:
            self.selected_preview_index_by_slice[z] = selected_preview
            self.selected_overlay_index_by_slice[z] = -1
            self.annotation_hint.set("Selected preview mask: Accept Current to commit, Reject Current to remove")
            self.render_current_slice()
            return

        overlays = self.overlays_by_slice.get(z, [])
        view_layer = self.get_active_view_layer()
        selected = -1
        for idx in range(len(overlays) - 1, -1, -1):
            overlay = overlays[idx]
            if view_layer != "All" and overlay.get("layer", "Layer 1") != view_layer:
                continue
            if self.point_in_polygon(image_pt, overlay["points"]):
                selected = idx
                break
        self.selected_overlay_index_by_slice[z] = selected
        self.selected_preview_index_by_slice[z] = -1
        if selected >= 0:
            ov = overlays[selected]
            self.mask_label_var.set(ov.get("label", "Default"))
            self.mask_color_var.set(ov.get("color", "#ff0000"))
            self.mask_layer_var.set(ov.get("layer", "Layer 1"))
            self.annotation_hint.set("Selected committed mask")
        else:
            self.annotation_hint.set("No mask selected")
        self.render_current_slice()

    def context_set_selected_label(self):
        if self.volume is None:
            return
        z = self.slice_index
        overlays = self.overlays_by_slice.get(z, [])
        idx = self.selected_overlay_index_by_slice.get(z, -1)
        if idx < 0 or idx >= len(overlays):
            return
        cur = overlays[idx].get("label", "Default")
        value = simpledialog.askstring("Set Label", "Label name:", initialvalue=cur, parent=self.root)
        if value is None:
            return
        self.mask_label_var.set(value.strip() or "Default")
        self.apply_metadata_to_selected_overlay()

    def context_set_selected_color(self):
        if self.volume is None:
            return
        self.pick_mask_color()
        self.apply_metadata_to_selected_overlay()

    def context_set_selected_layer(self):
        if self.volume is None:
            return
        z = self.slice_index
        overlays = self.overlays_by_slice.get(z, [])
        idx = self.selected_overlay_index_by_slice.get(z, -1)
        if idx < 0 or idx >= len(overlays):
            return
        cur = overlays[idx].get("layer", "Layer 1")
        value = simpledialog.askstring("Set Layer", "Layer name:", initialvalue=cur, parent=self.root)
        if value is None:
            return
        self.mask_layer_var.set(self.normalize_layer_name(value))
        self.apply_metadata_to_selected_overlay()

    def clear_selected_overlay(self):
        self.delete_selected_overlay_only()

    def delete_selected_overlay_and_mask(self):
        self.delete_selected_overlay_only()

    def delete_selected_overlay_only(self):
        z = self.slice_index
        preview_idx = self.selected_preview_index_by_slice.get(z, -1)
        preview_overlays = self.preview_overlays_by_slice.get(z, [])
        if 0 <= preview_idx < len(preview_overlays):
            self.reject_preview_current()
            return
        overlays = self.overlays_by_slice.get(z, [])
        masks = self.masks_by_slice.get(z, [])
        if not overlays:
            return
        idx = self.selected_overlay_index_by_slice.get(z, len(overlays) - 1)
        if idx < 0 or idx >= len(overlays):
            idx = len(overlays) - 1
        removed_overlay = overlays[idx]
        removed_mask = masks[idx] if idx < len(masks) else None
        selected_before = self.selected_overlay_index_by_slice.get(z, -1)

        def do():
            if idx < len(overlays):
                overlays.pop(idx)
            if idx < len(masks):
                masks.pop(idx)
            self.selected_overlay_index_by_slice[z] = min(idx, len(overlays) - 1) if overlays else -1
            self.refresh_layer_options()

        def undo():
            overlays.insert(idx, removed_overlay)
            if removed_mask is not None:
                masks.insert(idx, removed_mask)
            self.selected_overlay_index_by_slice[z] = selected_before
            self.refresh_layer_options()

        self.execute_command(do, undo)
        self.render_current_slice()

    def cancel_current_polygon(self):
        if self.current_polygon:
            points = [[int(x), int(y)] for x, y in self.current_polygon]
            self.current_polygon = []
            if self.annotation_mode:
                self.annotation_hint.set("Annotate: current polygon canceled")
            self.log_gui_event("manual_polygon_cancelled", points=points)
            self.render_current_slice()

    def execute_command(self, do_fn, undo_fn):
        do_fn()
        self.undo_stack.append((do_fn, undo_fn))
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        do_fn, undo_fn = self.undo_stack.pop()
        undo_fn()
        self.redo_stack.append((do_fn, undo_fn))
        self.render_current_slice()

    def redo(self):
        if not self.redo_stack:
            return
        do_fn, undo_fn = self.redo_stack.pop()
        do_fn()
        self.undo_stack.append((do_fn, undo_fn))
        self.render_current_slice()

    @staticmethod
    def point_in_polygon(point, polygon):
        x, y = point
        inside = False
        n = len(polygon)
        if n < 3:
            return False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / float((yj - yi) if (yj - yi) != 0 else 1e-9) + xi
            )
            if intersects:
                inside = not inside
            j = i
        return inside

    def on_app_close(self):
        self.log_gui_event("app_close")
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ContourAnnotationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
