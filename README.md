# Medical Contour Annotation Tool

Desktop medical contour annotation for 3D NIfTI volumes. The application lives in `python_app/` (Tkinter).

## Quick Start (Windows)

```powershell
python_app\run_python_app.bat
```

Or manually:

```powershell
python -m pip install -r python_app\requirements.txt
python python_app\main.py
```

## Python Dependencies

- `numpy`
- `nibabel`
- `pillow`
- `opencv-python-headless`

## Core Features

- 3D NIfTI loading (`.nii` / `.nii.gz`) with slice browsing
- Window/Level + Threshold + Opaque controls
- Polygon annotation with undo/redo
- Selection-based delete/edit of overlays
- Label/color/layer metadata per mask
- Layer filtering (`View Layer`)
- Watershed + Levelset (current/all, preview/apply)
- Export masks to PNG and NIfTI

## Annotation UX

- `Start Annotation` to enter draw mode
- Left click: add polygon points
- Finish polygon: `Double-click`, `Enter`, `Right-click`, or `Finish Polygon`
- Cancel current polygon: `Esc` or `Cancel Polygon`
- Right-click selected overlay for context actions:
  - delete
  - set label
  - set color
  - set layer

## AI Backends

`AI Agent` tab supports:

- `LangSAM` (text prompt segmentation)
- `MedSAM` (2D prompt-driven path)
- `MedSAM2` (3D volume path)

### LangSAM Notes

`LangSAM` is used for text-prompt segmentation and can also generate sparse text seeds for MedSAM2 3D propagation.

Repository/reference:

- [luca-medeiros/lang-segment-anything](https://github.com/luca-medeiros/lang-segment-anything)

### MedSAM Command Bridge (2D)

Set `MedSAM Cmd` in UI to an external command implementing:

```text
<cmd> --input <input.npy> --request <request.json> --output <output.npy>
```

- input: 2D `(H, W)` uint8 slice
- output: `(H, W)` or `(N, H, W)` binary mask(s)

Stub included:

- `python_app/medsam_bridge_stub.py`

### MedSAM2 Command Bridge (3D)

Set `MedSAM2 Cmd` in UI to an external command implementing:

```text
<cmd> --mode volume --input <input_volume.npy> --request <request.json> --output <output_volume.npy>
```

- input: 3D `(Z, H, W)` uint8 volume
- output: 3D `(Z, H, W)` binary mask volume

Stub included:

- `python_app/medsam2_bridge_stub.py`

## MedSAM2 3D Workflow (Recommended)

1. Draw committed masks on a few key slices (seed slices)
2. In `AI Agent`, select `MedSAM2`
3. Enable `Use 3D Seed Prompts`
4. Optional: set `Seed Labels` (`All` or comma-separated labels like `liver,tumor`)
5. Optional: enable `Use LangSAM Text Seeds` and set `LangSAM Seed Stride`
6. Run `Preview All` or `Apply All`

The app supports hybrid prompts for MedSAM2:

- manual seed volume (from committed masks)
- optional LangSAM text seeds
- optional current-slice bbox anchor
- internal seed densification/propagation before bridge inference

## UI / Rendering Notes

- Left control pane is scrollable (scrollbar + mouse wheel)
- Overlays are alpha-composited over base slice (does not erase base image)
- `Opaque` controls overlay transparency for committed and preview masks
- `Show Committed` / `Show Preview` control overlay layers independently
