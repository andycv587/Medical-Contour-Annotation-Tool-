from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import nibabel as nib
import numpy as np
from PIL import Image, ImageSequence

from app.configs.io import configured, find_not_configured, load_structured_config, resolve_path


class DatasetConfigurationError(RuntimeError):
    def __init__(self, message: str, missing: Optional[List[str]] = None):
        super().__init__(message)
        self.missing = missing or []


@dataclass
class BenchmarkCase:
    case_id: str
    image_path: Optional[str]
    mask_path: Optional[str]
    image_array: np.ndarray
    gt_mask: np.ndarray
    modality: str
    dataset_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["image_shape"] = list(np.asarray(self.image_array).shape)
        data["gt_shape"] = list(np.asarray(self.gt_mask).shape)
        data.pop("image_array", None)
        data.pop("gt_mask", None)
        return data

    def legacy_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "image": self.image_array,
            "gt": self.gt_mask,
            "prompt": self.metadata.get("prompt"),
            "bbox": self.metadata.get("bbox"),
            "metadata": dict(self.metadata, modality=self.modality, dataset_name=self.dataset_name),
            "image_path": self.image_path,
            "mask_path": self.mask_path,
        }


def synthetic_organ_case(seed: int = 7) -> BenchmarkCase:
    rng = np.random.default_rng(seed)
    z, h, w = 12, 96, 96
    zz, yy, xx = np.mgrid[:z, :h, :w]
    center = np.array([z * 0.52, h * 0.50, w * 0.47])
    radii = np.array([3.8, 24.0, 18.0])
    gt = (((zz - center[0]) / radii[0]) ** 2 + ((yy - center[1]) / radii[1]) ** 2 + ((xx - center[2]) / radii[2]) ** 2) <= 1.0
    image = rng.normal(28, 5, size=(z, h, w)).astype(np.float32)
    image += (yy / h * 12).astype(np.float32)
    image[gt] = rng.normal(190, 10, size=int(np.count_nonzero(gt))).astype(np.float32)
    image = np.clip(image, 0, 255).astype(np.uint8)
    bbox = bbox_from_mask(gt[z // 2])
    return BenchmarkCase(
        case_id="synthetic_organ_3d",
        image_path=None,
        mask_path=None,
        image_array=image,
        gt_mask=gt.astype(np.uint8),
        modality="synthetic_nifti",
        dataset_name="synthetic_smoke",
        metadata={"prompt": "liver lesion", "bbox": bbox, "synthetic": True},
    )


def synthetic_cell_case(seed: int = 11) -> BenchmarkCase:
    rng = np.random.default_rng(seed)
    h, w = 128, 128
    image = rng.normal(22, 4, size=(h, w)).astype(np.float32)
    gt = np.zeros((h, w), dtype=np.uint16)
    centers: List[tuple[int, int]] = []
    for _ in range(22):
        for _attempt in range(80):
            y = int(rng.integers(14, h - 14))
            x = int(rng.integers(14, w - 14))
            if all((x - cx) ** 2 + (y - cy) ** 2 > 13 ** 2 for cy, cx in centers):
                centers.append((y, x))
                break
    label = 1
    for y, x in centers:
        radius = int(rng.integers(5, 9))
        cv2.circle(gt, (x, y), radius, label, -1)
        cv2.circle(image, (x, y), radius, float(rng.normal(190, 14)), -1)
        cv2.circle(image, (x, y), max(1, radius // 2), float(rng.normal(230, 10)), -1)
        label += 1
    image = cv2.GaussianBlur(image, (3, 3), 0)
    image += rng.normal(0, 5, size=(h, w)).astype(np.float32)
    return BenchmarkCase(
        case_id="synthetic_cells_2d",
        image_path=None,
        mask_path=None,
        image_array=np.clip(image, 0, 255).astype(np.uint8),
        gt_mask=gt,
        modality="microscopy",
        dataset_name="synthetic_smoke",
        metadata={"prompt": "cells nuclei", "bbox": None, "synthetic": True},
    )


def synthetic_smoke_cases() -> List[BenchmarkCase]:
    return [synthetic_organ_case(), synthetic_cell_case()]


def load_dataset_manifest(path: str) -> Dict[str, Any]:
    """Load a dataset manifest without resolving or requiring real files."""
    return load_structured_config(path)


def validate_dataset_manifest(path: str) -> Dict[str, Any]:
    """Summarize whether dataset templates are configured enough for real runs."""
    manifest = load_dataset_manifest(path)
    entries = list(_iter_dataset_manifest_entries(manifest))
    configured_count = 0
    for section, entry in entries:
        _ = section
        images = entry.get("images_dir", "")
        masks = entry.get("masks_dir", "")
        if configured(images) and configured(masks):
            configured_count += 1
    return {
        "path": path,
        "dataset_count": len(entries),
        "configured_count": configured_count,
        "not_configured_fields": find_not_configured(manifest),
    }


def _iter_dataset_manifest_entries(manifest: Dict[str, Any]):
    datasets = manifest.get("datasets", manifest)
    for section in ("medical_3d", "microscopy"):
        value = datasets.get(section, [])
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict):
                    yield section, entry
        elif isinstance(value, dict):
            for entry in value.values():
                if isinstance(entry, dict):
                    yield section, entry


def load_cases_from_registry(
    registry_path: str,
    *,
    experiment: str,
    max_cases: Optional[int] = None,
    target_label: Optional[int] = None,
    channel: Optional[int] = None,
    instance_masks: Optional[bool] = None,
) -> List[BenchmarkCase]:
    registry = load_structured_config(registry_path)
    entry, entry_key = resolve_dataset_entry(registry, experiment)
    if experiment == "medical_3d":
        return load_medical_3d_cases(entry, entry_key=entry_key, max_cases=max_cases, target_label=target_label)
    if experiment == "microscopy":
        return load_microscopy_cases(entry, entry_key=entry_key, max_cases=max_cases, channel=channel, instance_masks=instance_masks)
    raise DatasetConfigurationError(f"unsupported experiment dataset type: {experiment}", [f"datasets.{experiment}"])


def resolve_dataset_entry(registry: Dict[str, Any], experiment: str) -> tuple[Dict[str, Any], str]:
    datasets = registry.get("datasets", registry)
    section = datasets.get(experiment)
    if not isinstance(section, dict):
        raise DatasetConfigurationError(f"dataset registry has no '{experiment}' section", [f"datasets.{experiment}"])
    for key, value in section.items():
        if isinstance(value, dict):
            return value, str(key)
    raise DatasetConfigurationError(f"dataset section '{experiment}' has no dataset entries", [f"datasets.{experiment}"])


def load_medical_3d_cases(
    dataset: Dict[str, Any],
    *,
    entry_key: str = "medical_3d",
    max_cases: Optional[int] = None,
    target_label: Optional[int] = None,
) -> List[BenchmarkCase]:
    images_dir, masks_dir = _resolve_pair_dirs(dataset)
    image_pattern = str(dataset.get("image_pattern", "*.nii.gz"))
    mask_pattern = str(dataset.get("mask_pattern", "*.nii.gz"))
    image_files = sorted(images_dir.glob(image_pattern))
    mask_files = sorted(masks_dir.glob(mask_pattern))
    _require_files(image_files, "images_dir", image_pattern)
    _require_files(mask_files, "masks_dir", mask_pattern)
    mask_by_key = {_case_key(path): path for path in mask_files}
    cases: List[BenchmarkCase] = []
    for image_path in image_files:
        key = _case_key(image_path)
        mask_path = mask_by_key.get(key)
        if mask_path is None:
            continue
        img_nii = nib.load(str(image_path))
        mask_nii = nib.load(str(mask_path))
        image = np.asarray(img_nii.get_fdata(dtype=np.float32))
        gt_raw = np.asarray(mask_nii.get_fdata()).astype(np.int32)
        if image.shape != gt_raw.shape:
            raise DatasetConfigurationError(f"shape mismatch for {image_path.name}: image {image.shape}, mask {gt_raw.shape}")
        label = target_label if target_label is not None else _coerce_optional_int(dataset.get("target_label"))
        if label == -1:
            gt = (gt_raw > 0).astype(np.uint8)
            label_for_metadata = "all_nonzero"
        else:
            gt = (gt_raw == int(label)).astype(np.uint8) if label is not None else gt_raw.astype(np.uint16)
            label_for_metadata = label
        metadata = {
            "dataset_entry": entry_key,
            "task_name": dataset.get("task_name", entry_key),
            "split": dataset.get("split", ""),
            "target_label": label_for_metadata,
            "affine": img_nii.affine.tolist(),
            "zooms": list(img_nii.header.get_zooms()),
            "orientation_axcodes": _orientation_axcodes(img_nii),
            "source_url": dataset.get("source_url", ""),
            "license": dataset.get("license", ""),
            "citation": dataset.get("citation", ""),
        }
        cases.append(
            BenchmarkCase(
                case_id=key,
                image_path=str(image_path),
                mask_path=str(mask_path),
                image_array=image,
                gt_mask=gt,
                modality="medical_3d",
                dataset_name=str(dataset.get("task_name") or entry_key),
                metadata=metadata,
            )
        )
        if max_cases is not None and len(cases) >= max_cases:
            break
    if not cases:
        raise DatasetConfigurationError("no paired medical 3D image/mask cases found", ["images_dir", "masks_dir"])
    return cases


def load_microscopy_cases(
    dataset: Dict[str, Any],
    *,
    entry_key: str = "microscopy",
    max_cases: Optional[int] = None,
    channel: Optional[int] = None,
    instance_masks: Optional[bool] = None,
) -> List[BenchmarkCase]:
    images_dir, masks_dir = _resolve_pair_dirs(dataset)
    image_pattern = str(dataset.get("image_pattern", "*.png"))
    mask_pattern = str(dataset.get("mask_pattern", "*.png"))
    image_files = sorted(images_dir.glob(image_pattern))
    mask_files = sorted(masks_dir.glob(mask_pattern))
    _require_files(image_files, "images_dir", image_pattern)
    _require_files(mask_files, "masks_dir", mask_pattern)
    mask_by_key = {_case_key(path): path for path in mask_files}
    cases: List[BenchmarkCase] = []
    for image_path in image_files:
        key = _case_key(image_path)
        mask_path = mask_by_key.get(key)
        if mask_path is None:
            continue
        image = _load_image_file(image_path)
        mask = _load_image_file(mask_path)
        if mask.ndim == 3:
            mask = mask[..., 0]
        selected_channel = channel if channel is not None else _coerce_optional_int(dataset.get("channel"))
        if selected_channel is not None and image.ndim == 3:
            image = image[..., int(selected_channel)]
        if image.ndim == 3:
            image_for_shape = image[..., 0]
        else:
            image_for_shape = image
        if image_for_shape.shape[:2] != mask.shape[:2]:
            raise DatasetConfigurationError(f"shape mismatch for {image_path.name}: image {image_for_shape.shape}, mask {mask.shape}")
        is_instance = bool(dataset.get("instance_masks", True) if instance_masks is None else instance_masks)
        metadata = {
            "dataset_entry": entry_key,
            "dataset_name": dataset.get("dataset_name", entry_key),
            "instance_masks": is_instance,
            "channel": selected_channel,
            "source_url": dataset.get("source_url", ""),
            "license": dataset.get("license", ""),
            "citation": dataset.get("citation", ""),
        }
        cases.append(
            BenchmarkCase(
                case_id=key,
                image_path=str(image_path),
                mask_path=str(mask_path),
                image_array=np.asarray(image),
                gt_mask=np.asarray(mask),
                modality="microscopy",
                dataset_name=str(dataset.get("dataset_name") or entry_key),
                metadata=metadata,
            )
        )
        if max_cases is not None and len(cases) >= max_cases:
            break
    if not cases:
        raise DatasetConfigurationError("no paired microscopy image/mask cases found", ["images_dir", "masks_dir"])
    return cases


def bbox_from_mask(mask):
    arr = np.asarray(mask)
    ys, xs = np.where(arr > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def center_point_from_mask(mask):
    arr = np.asarray(mask)
    ys, xs = np.where(arr > 0)
    if ys.size == 0 or xs.size == 0:
        return None
    return [[float(xs.mean()), float(ys.mean())]]


def _resolve_pair_dirs(dataset: Dict[str, Any]) -> tuple[Path, Path]:
    missing: List[str] = []
    data_root = str(dataset.get("data_root", ""))
    images_value = str(dataset.get("images_dir", ""))
    masks_value = str(dataset.get("masks_dir", ""))
    if not configured(data_root):
        missing.append("data_root")
    if not configured(images_value):
        missing.append("images_dir")
    if not configured(masks_value):
        missing.append("masks_dir")
    if missing:
        raise DatasetConfigurationError("dataset registry contains NOT_CONFIGURED paths", missing)
    root = Path(data_root)
    images_dir = Path(resolve_path(images_value, base_dir=str(root)))
    masks_dir = Path(resolve_path(masks_value, base_dir=str(root)))
    missing_paths = []
    if not images_dir.exists():
        missing_paths.append(f"images_dir does not exist: {images_dir}")
    if not masks_dir.exists():
        missing_paths.append(f"masks_dir does not exist: {masks_dir}")
    if missing_paths:
        raise DatasetConfigurationError("; ".join(missing_paths), missing_paths)
    return images_dir, masks_dir


def _require_files(files: List[Path], field: str, pattern: str) -> None:
    if not files:
        raise DatasetConfigurationError(f"no files found in {field} with pattern {pattern}", [field])


def _case_key(path: Path) -> str:
    name = path.name
    for suffix in (".nii.gz", ".nii", ".ome.tif", ".ome.tiff", ".tiff", ".tif", ".png", ".jpg", ".jpeg"):
        if name.lower().endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def _coerce_optional_int(value: Any) -> Optional[int]:
    if value is None or value == "" or str(value).startswith("TO_BE") or str(value) == "NOT_CONFIGURED":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _orientation_axcodes(img) -> List[str]:
    try:
        return list(nib.aff2axcodes(img.affine))
    except Exception:
        return []


def _load_image_file(path: Path) -> np.ndarray:
    with Image.open(path) as img:
        frames = [np.asarray(frame.copy()) for frame in ImageSequence.Iterator(img)]
    if len(frames) > 1:
        return np.stack(frames, axis=0)
    return np.asarray(frames[0])
