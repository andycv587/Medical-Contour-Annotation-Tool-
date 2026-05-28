# DICOM SEG / RTSTRUCT Limitations

The current package does not implement DICOM SEG or RTSTRUCT export.

Reasons:

- Correct DICOM SEG and RTSTRUCT export requires preserving clinical image geometry, study/series metadata, frame of reference UIDs, coded segment terminology, and modality-specific coordinate transforms.
- The current lightweight app can load NIfTI and common microscopy/image formats, but it does not yet include a DICOM series importer or DICOM metadata model.
- Incorrect DICOM SEG/RTSTRUCT output could be misleading in clinical workflows.

Current supported interoperability formats:

- PNG masks for 2D masks.
- NIfTI masks for 3D medical volumes.
- TIFF stacks for 2D/3D mask stacks.
- COCO JSON for 2D instance masks.
- Simple polygon/contour JSON.

Future work:

- Add DICOM import through `pydicom`/SimpleITK.
- Preserve frame of reference and segment coded metadata.
- Export DICOM SEG through `highdicom` or an equivalent validated library.
- Export RTSTRUCT only after contour-to-patient-coordinate conversion is validated against a reference TPS/viewer.
