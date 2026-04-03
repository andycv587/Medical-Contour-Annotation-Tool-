# Medical Contour Annotation Tool

## Python App (Current Main Workflow)

The active desktop workflow is now in `python_app/` (Tkinter-based). The legacy Java app is still in the repo for reference.

### Quick Start (Windows)

```powershell
python_app\run_python_app.bat
```

Or manually:

```powershell
python -m pip install -r python_app\requirements.txt
python python_app\main.py
```

### Python Dependencies

- `numpy`
- `nibabel`
- `pillow`
- `opencv-python-headless`

### Core Features Implemented

- 3D NIfTI loading (`.nii` / `.nii.gz`) with slice browsing
- Window/Level + Threshold + Opaque controls
- Polygon annotation with undo/redo
- Selection-based delete/edit of overlays
- Label/color/layer metadata per mask
- Layer filtering (`View Layer`)
- Watershed + Levelset (current/all, preview/apply)
- Export masks to PNG and NIfTI

### Annotation UX

- `Start Annotation` to enter draw mode
- Left click: add polygon points
- Finish polygon: `Double-click`, `Enter`, `Right-click`, or `Finish Polygon`
- Cancel current polygon: `Esc` or `Cancel Polygon`
- Right-click selected overlay for context actions:
  - delete
  - set label
  - set color
  - set layer

### AI Backends

`AI Agent` tab supports:

- `LangSAM` (text prompt segmentation)
- `MedSAM` (2D prompt-driven path)
- `MedSAM2` (3D volume path)

#### LangSAM Notes

`LangSAM` is used for text-prompt segmentation and can also generate sparse text seeds for MedSAM2 3D propagation.

Repository/reference:
- [luca-medeiros/lang-segment-anything](https://github.com/luca-medeiros/lang-segment-anything)

#### MedSAM Command Bridge (2D)

Set `MedSAM Cmd` in UI to an external command implementing:

```text
<cmd> --input <input.npy> --request <request.json> --output <output.npy>
```

- input: 2D `(H, W)` uint8 slice
- output: `(H, W)` or `(N, H, W)` binary mask(s)

Stub included:
- `python_app/medsam_bridge_stub.py`

#### MedSAM2 Command Bridge (3D)

Set `MedSAM2 Cmd` in UI to an external command implementing:

```text
<cmd> --mode volume --input <input_volume.npy> --request <request.json> --output <output_volume.npy>
```

- input: 3D `(Z, H, W)` uint8 volume
- output: 3D `(Z, H, W)` binary mask volume

Stub included:
- `python_app/medsam2_bridge_stub.py`

### MedSAM2 3D Workflow (Recommended)

1. Draw committed masks on a few key slices (seed slices)
2. In `AI Agent`, select `MedSAM2`
3. Enable `Use 3D Seed Prompts`
4. Optional: set `Seed Labels` (`All` or comma-separated labels like `liver,tumor`)
5. Optional: enable `Use LangSAM Text Seeds` and set `LangSAM Seed Stride`
6. Run `Preview All` or `Apply All`

The app now supports hybrid prompts for MedSAM2:
- manual seed volume (from committed masks)
- optional LangSAM text seeds
- optional current-slice bbox anchor
- internal seed densification/propagation before bridge inference

### UI/Rendering Notes

- Left control pane is scrollable (scrollbar + mouse wheel)
- Overlays are alpha-composited over base slice (does not erase base image)
- `Opaque` controls overlay transparency for committed and preview masks
- `Show Committed` / `Show Preview` control overlay layers independently

---

## Developer Notes (Windows)

### Prerequisites

- Java 8 runtime (project target is Java 8)
- NetBeans/Ant project support
- OpenCV Java native library available by one of these options:
  - Set `OPENCV_LIB_PATH` (or `-Dopencv.lib.path=...`) to a full library file path or folder
  - Keep bundled OpenCV loading enabled (default, via `nu.pattern.OpenCV`)
  - Ensure OpenCV is discoverable via `java.library.path`

### OpenCV Loading Order

The app now uses `Contours.core.OpenCVLoader` and attempts OpenCV in this order:

1. Explicit configured path (`opencv.lib.path` / `OPENCV_LIB_PATH`)
2. Bundled loader (`nu.pattern.OpenCV`) when enabled
3. `System.loadLibrary(...)` fallback candidates (`opencv_java490`, `opencv_java341`, `opencv_java`)

Optional toggle:

- `-Dopencv.preferBundled=false` (or `OPENCV_PREFER_BUNDLED=false`) to skip bundled loading and rely on system libraries.

### Build / Run

From project root:

```powershell
javac --release 8 -cp "libs/opencv-4.9.0-0.jar;libs/jama-1.0.3.jar" -d build/classes (Get-ChildItem -Recurse -Filter *.java src | ForEach-Object { $_.FullName })
java -cp "build/classes;libs/opencv-4.9.0-0.jar;libs/jama-1.0.3.jar" Contours.annotation.WindowDesign
```

Run smoke tests through Ant:

```powershell
ant smoke-test
```

### Architecture Direction

- UI layer remains in Swing (`Contours.annotation`)
- Core contracts/config in `Contours.core`
- Session/state layer is in `Contours.core.session`
  - `VolumeSession`: loaded volumes and slice state
  - `AnnotationSession`: active label, generated overlays/contours, command stack, last request snapshots
- Algorithm layer is in `Contours.algorithms`
  - `WatershedSegmentationAlgorithm`
  - `HessianSegmentationAlgorithm`
  - `LevelsetSegmentationAlgorithm`
- Algorithm resolution is centralized in `Contours.core.SegmentationAlgorithmFactory`
  - Enum key: `Contours.core.AlgorithmType`
  - Current registrations: `WATERSHED`, `HESSIAN`, `LEVELSET`
- Application orchestration/use-case layer is in `Contours.application`
  - `SegmentationController`
  - `NavigationController`
  - `ExportController`
- This is intended to make MedSAM / MedSAM2 / nnInteractive backends pluggable in later phases.

### SegmentationAlgorithm Plugin Contract

- Implement `Contours.core.SegmentationAlgorithm`
- Accept runtime inputs from `SegmentationRequest`
- Return standard `SegmentationResult`
  - Use strongly typed request DTOs under `Contours.core.request`:
    - `WatershedRequestPayload`
    - `HessianRequestPayload`
    - `LevelsetRequestPayload`
  - Access request payload with `request.getPayload(PayloadType.class)`
  - Use strongly typed payload DTOs under `Contours.core.payload`:
    - `WatershedResultPayload`
    - `HessianResultPayload`
    - `LevelsetResultPayload`
  - Access payload with `result.getPayload(PayloadType.class)`

Future MedSAM integration should attach here:

1. Add `MedSamSegmentationAlgorithm` under `Contours.algorithms`
2. Add `AlgorithmType.MEDSAM` and register it in `SegmentationAlgorithmFactory`
3. Build a typed request DTO from UI interaction (points/boxes, slice, image)
4. Return overlays or mask payload through a typed `SegmentationPayload` DTO
5. Keep Swing rendering in UI layer (`WindowDesign`) and avoid model-specific code in button handlers

### End-to-End Typed Flow

- `WindowDesign` reads user input and calls centralized parser:
  - `SegmentationRequestPayloadParser` -> `ValidationResult<T>`
- On valid input, UI sends typed request DTO via `SegmentationRequest`.
- `SegmentationController` resolves algorithm using `AlgorithmType` + `SegmentationAlgorithmFactory`.
- Algorithm returns typed result DTO through `SegmentationResult`.
- Controller applies command-based mutations and updates sessions.

### Navigation Ownership

- `VolumeSession` is the practical source of truth for slice navigation state.
- `NavigationController` is the navigation gateway used by:
  - wheel-driven slice changes
  - scrollbar-driven slice changes
  - slice index helpers used by segmentation apply paths
- `WindowDesign.pagenum` remains a compatibility shim and is synchronized from `VolumeSession`.

### Command / Undo Foundation

- Command abstraction is in `Contours.core.command`:
  - `AnnotationCommand`
  - `CommandStack`
  - Initial concrete commands:
    - `ApplySliceOverlayCommand`
    - `AddFreehandContourCommand`
    - `ClearOverlayCommand`
- Current real wiring:
  - Levelset overlay application uses `CommandStack` via `ApplySliceOverlayCommand`.
  - Freehand contour completion uses `AddFreehandContourCommand`.
  - Watershed overlay application uses `ApplyWatershedOverlaysCommand`.
  - Clear/Delete label flows now use selection-based deletion commands:
    - `DeleteSelectedOverlayCommand`
    - `DeleteSelectedGeneratedMaskCommand`

### Selection Model

- `AnnotationSession` now tracks explicit index-based selection:
  - selected overlay index
  - selected generated mask index
  - selected contour index
- Mutation paths default to "latest item" only when no valid selection exists.

Current undo/redo limits:

- Not all mutation paths are command-wrapped yet.
- Undo/redo state is scoped to commandized actions and not yet surfaced with dedicated UI controls.

### Typed Request + Validation Flow

- UI text fields are parsed through `Contours.core.request.SegmentationRequestPayloadParser`.
- Parser returns structured `ValidationResult<T>` / `ValidationError` from `Contours.core.validation`.
- `WindowDesign` surfaces `ValidationResult.firstErrorMessage()` through existing warning dialogs.
- Real algorithm execution paths no longer rely on map-style request params.

### Session Ownership Notes

- `VolumeSession` is the source of truth for current slice index used by navigation helpers.
- `WindowDesign.pagenum` is still present for compatibility with older rendering code, and is synchronized from `VolumeSession`.
- `AnnotationSession` owns generated overlays/coordinates/mask metadata and recent algorithm request snapshots.

### Guardrails Against Deprecated Request APIs

- Legacy map-style `SegmentationRequest` APIs are deprecated and retained only for migration safety.
- Smoke guardrail test: `Contours.core.DeprecatedRequestApiGuardrailTest` fails if non-request classes use:
  - `getParam(...)`
  - `getIntParam(...)`
  - `getParams()`

### Result DTO Model

- `SegmentationResult` remains generic for success/failure and message.
- Payload is explicit and typed through `Contours.core.payload.SegmentationPayload`.
- UI layer should avoid map casting and consume DTOs directly.

### OpenCV Troubleshooting

If startup reports OpenCV load failure:

1. Check message output from `OpenCVLoader` for attempted strategies
2. Set one of:
   - `OPENCV_LIB_PATH=C:\path\to\opencv_java490.dll`
   - `-Dopencv.lib.path=C:\path\to\opencv_java490.dll`
   - or a folder containing the OpenCV dll
3. If bundled loading should be bypassed, set:
   - `OPENCV_PREFER_BUNDLED=false`
   - or `-Dopencv.preferBundled=false`
4. Ensure matching architecture (64-bit JVM with 64-bit OpenCV)
