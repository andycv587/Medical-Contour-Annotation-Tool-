import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser, simpledialog

import cv2
import nibabel as nib
import numpy as np
from PIL import Image, ImageTk
from PIL import ImageDraw
from ai_agents import build_agent_registry


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
        self.ai_agents = build_agent_registry()
        self.ai_agent_name = tk.StringVar(value="LangSAM")
        self.ai_prompt = tk.StringVar(value="organ")
        self.medsam_cmd = tk.StringVar(value=os.environ.get("MEDSAM_INFER_CMD", ""))
        self.medsam2_cmd = tk.StringVar(value=os.environ.get("MEDSAM2_INFER_CMD", ""))
        self.ai_use_drawn_prompt = tk.BooleanVar(value=False)
        self.ai_use_3d_seed_prompt = tk.BooleanVar(value=False)
        self.ai_use_langsam_text_seed = tk.BooleanVar(value=False)
        self.ai_langsam_stride = tk.IntVar(value=5)
        self.ai_seed_labels_var = tk.StringVar(value="All")
        self.ai_status = tk.StringVar(value="AI: idle")
        self.undo_stack = []
        self.redo_stack = []
        self._view_origin_x = 0
        self._view_origin_y = 0
        self._view_width = 1
        self._view_height = 1

        self._build_ui()

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
        tk.Button(file_box, text="Choose Nifti", command=self.choose_nifti).grid(row=0, column=1)
        tk.Entry(file_box, textvariable=self.mask_path_var).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(6, 0))
        tk.Button(file_box, text="Choose Masks", command=self.choose_mask).grid(row=1, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export PNG Masks", command=self.export_png_masks).grid(row=2, column=1, pady=(6, 0))
        tk.Button(file_box, text="Export NIfTI Mask", command=self.export_nifti_mask).grid(row=3, column=1, pady=(6, 0))
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
            values=sorted(list(self.ai_agents.keys())),
            width=12,
            state="readonly",
        )
        ai_backend_combo.grid(row=0, column=1, sticky="ew")
        ai_backend_combo.bind("<<ComboboxSelected>>", self.on_ai_backend_changed)
        tk.Label(ai_form, text="Prompt").grid(row=1, column=0, sticky="w")
        tk.Entry(ai_form, textvariable=self.ai_prompt).grid(row=1, column=1, sticky="ew")
        tk.Label(ai_form, text="MedSAM Cmd").grid(row=2, column=0, sticky="w")
        tk.Entry(ai_form, textvariable=self.medsam_cmd).grid(row=2, column=1, sticky="ew")
        tk.Label(ai_form, text="MedSAM2 Cmd").grid(row=3, column=0, sticky="w")
        tk.Entry(ai_form, textvariable=self.medsam2_cmd).grid(row=3, column=1, sticky="ew")
        tk.Checkbutton(ai_form, text="Use Drawn Mask Prompt (current slice)", variable=self.ai_use_drawn_prompt).grid(row=4, column=0, columnspan=2, sticky="w")
        tk.Checkbutton(ai_form, text="Use 3D Seed Prompts (from committed masks)", variable=self.ai_use_3d_seed_prompt).grid(
            row=5, column=0, columnspan=2, sticky="w"
        )
        tk.Checkbutton(ai_form, text="Use LangSAM Text Seeds (for MedSAM2)", variable=self.ai_use_langsam_text_seed).grid(
            row=6, column=0, columnspan=2, sticky="w"
        )
        tk.Label(ai_form, text="LangSAM Seed Stride").grid(row=7, column=0, sticky="w")
        tk.Spinbox(ai_form, from_=1, to=20, textvariable=self.ai_langsam_stride, width=10).grid(row=7, column=1, sticky="w")
        tk.Label(ai_form, text="Seed Labels").grid(row=8, column=0, sticky="w")
        tk.Entry(ai_form, textvariable=self.ai_seed_labels_var).grid(row=8, column=1, sticky="ew")
        tk.Label(ai_form, text="(comma-separated, or All)", anchor="w").grid(row=9, column=0, columnspan=2, sticky="w")
        tk.Button(ai_form, text="Check Backend", command=self.check_ai_backend).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ai_form.columnconfigure(1, weight=1)

        ai_actions = tk.LabelFrame(ai, text="AI Actions", padx=6, pady=6)
        ai_actions.pack(fill="x", padx=6, pady=(0, 4))
        tk.Button(ai_actions, text="Preview Current", command=self.preview_ai_current).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Preview All", command=self.preview_ai_all).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Apply Current", command=self.apply_ai_current).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Apply All", command=self.apply_ai_all).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Accept Preview", command=self.accept_preview_current).pack(fill="x", pady=2)
        tk.Button(ai_actions, text="Reject Preview", command=self.reject_preview_current).pack(fill="x", pady=2)

        ai_status_row = tk.Frame(ai)
        ai_status_row.pack(fill="x", padx=6, pady=(0, 8))
        tk.Label(ai_status_row, textvariable=self.ai_status, anchor="w").pack(fill="x")

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

    def choose_nifti(self):
        path = filedialog.askopenfilename(
            title="Choose NIfTI",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            nii = nib.load(path)
            data = np.asarray(nii.get_fdata(dtype=np.float32))
            data = np.squeeze(data)
            if data.ndim != 3:
                raise ValueError(f"Only 3D volumes are supported right now, got shape={data.shape}")

            # Put likely slice axis first (usually the smallest dimension count).
            slice_axis = int(np.argmin(np.array(data.shape)))
            data = np.moveaxis(data, slice_axis, 0)

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
            self.current_polygon = []
            self.set_annotation_mode(False)
            self.mask_layer_var.set("Layer 1")
            self.view_layer_var.set("All")
            self.undo_stack = []
            self.redo_stack = []
            self.nifti_path_var.set(path)
            self.shape_label.config(text=f"Shape: {tuple(self.volume.shape)}")
            self.win_min_scale.set(0)
            self.win_max_scale.set(1000)
            self.threshold_scale.set(0)
            self.update_window_labels()
            self.refresh_layer_options()
            self.render_current_slice()
        except Exception as ex:
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
            arr = (vol_mask[z] > 0).astype(np.uint8) * 255
            if np.any(arr):
                img = Image.fromarray(arr, mode="L")
                img.save(os.path.join(out_dir, f"mask_{z:04d}.png"))
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
        nii_mask = nib.Nifti1Image(restored.astype(np.uint8), affine=self.loaded_nifti.affine, header=self.loaded_nifti.header)
        nib.save(nii_mask, out_path)
        messagebox.showinfo("Export", f"Saved NIfTI mask:\n{out_path}")

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
        self.slice_index = max(0, min(self.volume.shape[0] - 1, self.slice_index + delta))
        self.render_current_slice()

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
        if self.show_preview_overlays.get():
            preview_overlays = self.preview_overlays_by_slice.get(z, [])
            for overlay in preview_overlays:
                pts = overlay["points"]
                if len(pts) < 3:
                    continue
                draw.polygon(pts, fill=(0, 255, 255, int(255 * self.opacity)), outline=(0, 255, 255, 240))
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
        # MedSAM/MedSAM2 should be prompt-driven by default unless 3D seed mode is explicitly selected.
        if self.ai_agent_name.get() in ("MedSAM", "MedSAM2") and not self.ai_use_3d_seed_prompt.get():
            return True
        return self.ai_use_drawn_prompt.get()

    def on_ai_backend_changed(self, _event=None):
        if self.ai_agent_name.get() == "MedSAM2":
            self.ai_use_3d_seed_prompt.set(True)
            self.ai_status.set("AI: MedSAM2 selected, 3D seed mode enabled.")

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
        if drawn_prompt_mask is not None and drawn_prompt_mask.shape == norm.shape:
            norm_for_agent = np.where(drawn_prompt_mask > 0, norm, 0).astype(np.uint8)
        request_payload = dict(request_data or {})
        if drawn_prompt_mask is not None and drawn_prompt_mask.shape == norm.shape:
            bbox = self.mask_to_bbox(drawn_prompt_mask)
            if bbox is not None:
                request_payload["bbox"] = bbox
        result = agent.predict(norm_for_agent, self.ai_prompt.get().strip(), request=request_payload)
        polygons = []
        for mask in result.masks:
            if mask is None:
                continue
            if mask.shape != norm.shape:
                continue
            effective_mask = mask.astype(np.uint8)
            if drawn_prompt_mask is not None and drawn_prompt_mask.shape == effective_mask.shape:
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
            return
        if mask_volume.ndim != 3:
            return
        z_count = min(self.volume.shape[0], mask_volume.shape[0])
        for z in range(z_count):
            mask = (mask_volume[z] > 0).astype(np.uint8)
            polys = self.mask_to_polygons(mask, min_area=self.get_segmentation_min_area())
            if polys:
                self.set_preview_for_slice(z, polys, mask.shape)
            else:
                self.clear_preview_for_slice(z)

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

    def preview_ai_current(self):
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        z = self.slice_index
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        polygons, image_shape, msg = self.compute_ai_polygons_for_slice(z, drawn_prompt_mask=prompt_mask)
        self.ai_status.set(f"AI: {msg or 'done'}")
        if not polygons:
            self.clear_preview_for_slice(z)
            self.render_current_slice()
            if msg:
                messagebox.showinfo("AI Agent", msg)
            return
        self.set_preview_for_slice(z, polygons, image_shape)
        self.render_current_slice()

    def preview_ai_all(self):
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        if self.ai_agent_name.get() == "MedSAM2" and not self.ai_use_3d_seed_prompt.get():
            messagebox.showwarning("AI Agent", "MedSAM2 volume mode requires 3D seed prompts. Enable 'Use 3D Seed Prompts'.")
            return
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        seed_masks = self.collect_seed_masks_by_slice() if self.ai_use_3d_seed_prompt.get() else {}
        if self.ai_use_3d_seed_prompt.get() and not seed_masks:
            messagebox.showwarning("AI Agent", "Need committed seed masks on a few slices for 3D seed prompt mode.")
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            agent = self.get_selected_ai_agent()
            if agent is not None and self.ai_agent_name.get() == "MedSAM2":
                vol_u8 = self.volume_to_uint8()
                request_payload = {"seed_mode": "3d"}
                status_parts = []
                if self.ai_use_3d_seed_prompt.get():
                    manual_seed_vol = self.seed_masks_to_volume(seed_masks)
                    status_parts.append(f"manual seeds: {len(seed_masks)} slice(s)")
                    if self.ai_use_langsam_text_seed.get():
                        langsam_seeds, seed_msg = self.collect_langsam_seed_masks_by_slice()
                        status_parts.append(seed_msg)
                        langsam_seed_vol = self.seed_masks_to_volume(langsam_seeds)
                        if langsam_seed_vol is not None:
                            manual_seed_vol = np.maximum(manual_seed_vol, langsam_seed_vol) if manual_seed_vol is not None else langsam_seed_vol
                    if manual_seed_vol is not None:
                        request_payload["seed_volume"] = self.densify_seed_volume(manual_seed_vol)
                anchor_mask = self.get_drawn_prompt_mask_for_current_slice()
                if anchor_mask is not None:
                    bbox = self.mask_to_bbox(anchor_mask)
                    if bbox is not None:
                        request_payload["bbox"] = bbox
                        request_payload["bbox_slice_index"] = int(self.slice_index)
                vr = agent.predict_volume(vol_u8, self.ai_prompt.get().strip(), request=request_payload)
                if vr.mask_volume is None:
                    self.ai_status.set(f"AI: {vr.message}")
                    messagebox.showwarning("AI Agent", vr.message)
                    return
                self.set_preview_from_mask_volume(vr.mask_volume)
                self.ai_status.set("AI: previewed 3D volume.")
                self.render_current_slice()
                if vr.message:
                    if status_parts:
                        messagebox.showinfo("AI Agent", f"{vr.message}\n" + "\n".join(status_parts))
                    else:
                        messagebox.showinfo("AI Agent", vr.message)
                return

            preview_count = 0
            last_msg = ""
            for z in range(self.volume.shape[0]):
                per_slice_prompt = self.build_3d_seed_prompt_mask_for_slice(z, seed_masks) if seed_masks else prompt_mask
                polygons, image_shape, msg = self.compute_ai_polygons_for_slice(
                    z, drawn_prompt_mask=per_slice_prompt, request_data={"seed_mode": "3d" if seed_masks else "2d"}
                )
                if msg:
                    last_msg = msg
                if polygons:
                    self.set_preview_for_slice(z, polygons, image_shape)
                    preview_count += 1
                else:
                    self.clear_preview_for_slice(z)
            self.ai_status.set(f"AI: previewed {preview_count} slice(s).")
            self.render_current_slice()
            if last_msg:
                messagebox.showinfo("AI Agent", f"Previewed {preview_count} slice(s).\n{last_msg}")
        finally:
            self.root.config(cursor="")

    def apply_ai_current(self):
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        z = self.slice_index
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        polygons, image_shape, msg = self.compute_ai_polygons_for_slice(z, drawn_prompt_mask=prompt_mask)
        self.ai_status.set(f"AI: {msg or 'done'}")
        if polygons:
            self.add_polygons_to_slice(z, polygons, image_shape)
        self.render_current_slice()
        if msg:
            messagebox.showinfo("AI Agent", msg)

    def apply_ai_all(self):
        if self.volume is None:
            messagebox.showwarning("AI Agent", "Load NIfTI first.")
            return
        if self.ai_agent_name.get() == "MedSAM2" and not self.ai_use_3d_seed_prompt.get():
            messagebox.showwarning("AI Agent", "MedSAM2 volume mode requires 3D seed prompts. Enable 'Use 3D Seed Prompts'.")
            return
        use_drawn_prompt = self.should_use_drawn_prompt_for_ai()
        prompt_mask = self.get_drawn_prompt_mask_for_current_slice() if use_drawn_prompt else None
        if use_drawn_prompt and prompt_mask is None:
            messagebox.showwarning("AI Agent", "Draw/select a mask on current slice first.")
            return
        seed_masks = self.collect_seed_masks_by_slice() if self.ai_use_3d_seed_prompt.get() else {}
        if self.ai_use_3d_seed_prompt.get() and not seed_masks:
            messagebox.showwarning("AI Agent", "Need committed seed masks on a few slices for 3D seed prompt mode.")
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            agent = self.get_selected_ai_agent()
            if agent is not None and self.ai_agent_name.get() == "MedSAM2":
                vol_u8 = self.volume_to_uint8()
                request_payload = {"seed_mode": "3d"}
                status_parts = []
                if self.ai_use_3d_seed_prompt.get():
                    manual_seed_vol = self.seed_masks_to_volume(seed_masks)
                    status_parts.append(f"manual seeds: {len(seed_masks)} slice(s)")
                    if self.ai_use_langsam_text_seed.get():
                        langsam_seeds, seed_msg = self.collect_langsam_seed_masks_by_slice()
                        status_parts.append(seed_msg)
                        langsam_seed_vol = self.seed_masks_to_volume(langsam_seeds)
                        if langsam_seed_vol is not None:
                            manual_seed_vol = np.maximum(manual_seed_vol, langsam_seed_vol) if manual_seed_vol is not None else langsam_seed_vol
                    if manual_seed_vol is not None:
                        request_payload["seed_volume"] = self.densify_seed_volume(manual_seed_vol)
                anchor_mask = self.get_drawn_prompt_mask_for_current_slice()
                if anchor_mask is not None:
                    bbox = self.mask_to_bbox(anchor_mask)
                    if bbox is not None:
                        request_payload["bbox"] = bbox
                        request_payload["bbox_slice_index"] = int(self.slice_index)
                vr = agent.predict_volume(vol_u8, self.ai_prompt.get().strip(), request=request_payload)
                if vr.mask_volume is None:
                    self.ai_status.set(f"AI: {vr.message}")
                    messagebox.showwarning("AI Agent", vr.message)
                    return
                apply_count = self.add_committed_from_mask_volume(vr.mask_volume)
                self.ai_status.set(f"AI: applied 3D volume on {apply_count} slice(s).")
                self.render_current_slice()
                if vr.message:
                    if status_parts:
                        messagebox.showinfo("AI Agent", f"{vr.message}\n" + "\n".join(status_parts))
                    else:
                        messagebox.showinfo("AI Agent", vr.message)
                return

            apply_count = 0
            last_msg = ""
            for z in range(self.volume.shape[0]):
                per_slice_prompt = self.build_3d_seed_prompt_mask_for_slice(z, seed_masks) if seed_masks else prompt_mask
                polygons, image_shape, msg = self.compute_ai_polygons_for_slice(
                    z, drawn_prompt_mask=per_slice_prompt, request_data={"seed_mode": "3d" if seed_masks else "2d"}
                )
                if msg:
                    last_msg = msg
                if polygons:
                    self.add_polygons_to_slice(z, polygons, image_shape)
                    apply_count += 1
            self.ai_status.set(f"AI: applied {apply_count} slice(s).")
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
        polygons, image_shape = self.compute_watershed_polygons_for_slice(z)
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
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            preview_count = 0
            for z in range(self.volume.shape[0]):
                polygons, image_shape = self.compute_watershed_polygons_for_slice(z)
                if polygons:
                    self.set_preview_for_slice(z, polygons, image_shape)
                    preview_count += 1
                else:
                    self.clear_preview_for_slice(z)
            self.render_current_slice()
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
        polygons, image_shape = self.compute_levelset_polygons_for_slice(z)
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
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            preview_count = 0
            for z in range(self.volume.shape[0]):
                polygons, image_shape = self.compute_levelset_polygons_for_slice(z)
                if polygons:
                    self.set_preview_for_slice(z, polygons, image_shape)
                    preview_count += 1
                else:
                    self.clear_preview_for_slice(z)
            self.render_current_slice()
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

    def clear_preview_for_slice(self, z: int):
        self.preview_overlays_by_slice.pop(z, None)
        self.preview_masks_by_slice.pop(z, None)

    def accept_preview_current(self):
        if self.volume is None:
            return
        z = self.slice_index
        preview_overlays = list(self.preview_overlays_by_slice.get(z, []))
        preview_masks = list(self.preview_masks_by_slice.get(z, []))
        if not preview_overlays:
            return
        overlays = self.overlays_by_slice.setdefault(z, [])
        masks = self.masks_by_slice.setdefault(z, [])
        selected_before = self.selected_overlay_index_by_slice.get(z, -1)

        def do():
            overlays.extend(preview_overlays)
            masks.extend(preview_masks)
            self.selected_overlay_index_by_slice[z] = len(overlays) - 1
            self.clear_preview_for_slice(z)
            self.refresh_layer_options()

        def undo():
            remove_count = len(preview_overlays)
            if remove_count > 0 and len(overlays) >= remove_count:
                del overlays[-remove_count:]
            if remove_count > 0 and len(masks) >= remove_count:
                del masks[-remove_count:]
            self.selected_overlay_index_by_slice[z] = selected_before
            self.refresh_layer_options()

        self.execute_command(do, undo)
        self.render_current_slice()

    def reject_preview_current(self):
        if self.volume is None:
            return
        self.clear_preview_for_slice(self.slice_index)
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
            self.refresh_layer_options()

        self.execute_command(do, undo)
        self.render_current_slice()

    def reject_preview_all(self):
        if self.volume is None:
            return
        self.preview_overlays_by_slice.clear()
        self.preview_masks_by_slice.clear()
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
        self.set_annotation_mode(not self.annotation_mode)
        if not self.annotation_mode:
            self.current_polygon = []
        self.render_current_slice()

    def set_annotation_mode(self, enabled: bool):
        self.annotation_mode = bool(enabled)
        if self.annotation_mode:
            self.annotation_button.config(text="Stop Annotation")
            self.annotation_hint.set("Annotate: ON | Left click add points | Double-click / Enter / Right-click finish | Esc cancel")
        else:
            self.annotation_button.config(text="Start Annotation")
            self.annotation_hint.set("Annotate: OFF | Click Start Annotation to draw polygon")

    def on_canvas_left_click(self, event):
        image_pt = self.canvas_to_image_point(event.x, event.y)
        if image_pt is None or self.volume is None:
            return
        if self.annotation_mode:
            self.current_polygon.append(image_pt)
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
        if selected >= 0:
            ov = overlays[selected]
            self.mask_label_var.set(ov.get("label", "Default"))
            self.mask_color_var.set(ov.get("color", "#ff0000"))
            self.mask_layer_var.set(ov.get("layer", "Layer 1"))
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
            self.current_polygon = []
            if self.annotation_mode:
                self.annotation_hint.set("Annotate: current polygon canceled")
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


def main():
    root = tk.Tk()
    app = ContourAnnotationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
