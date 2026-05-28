# Export Formats

Implemented export helpers live in `contour_io/exporters.py` and are wired into the Tkinter GUI.

| Format | Status | Notes |
|---|---|---|
| PNG mask slices | Implemented | Writes non-empty 2D mask slices and GUI provenance sidecars. |
| NIfTI mask | Implemented | Requires a loaded NIfTI source for affine/header reuse. |
| TIFF stack | Implemented | Supports 2D or 3D binary mask stacks. |
| Polygon JSON | Implemented | Stores slice-indexed polygons plus label/color/layer metadata. |
| COCO JSON | Implemented for current 2D slice | Requires current-slice committed instance-like masks. |
| OME-TIFF | Future/optional | Not claimed unless metadata-safe implementation and tests are added. |
| DICOM SEG | Future work | Not implemented. |
| RTSTRUCT | Future work | Not implemented. |

Unsupported exports should warn in the GUI and must not crash the session.
