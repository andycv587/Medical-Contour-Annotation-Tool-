from .base import BackendStatus, SegmentationBackend, SegmentationResult
from .classical_backend import ClassicalBackend
from .cellpose_backend import CellposeBackend
from .langsam_backend import LangSAMBackend
from .medsam_backend import MedSAMBackend
from .medsam2_backend import MedSAM2Backend
from .mock_backend import MockBackend


def build_default_backends():
    return {
        backend.name: backend
        for backend in (
            MockBackend(),
            ClassicalBackend(),
            LangSAMBackend(),
            MedSAMBackend(),
            MedSAM2Backend(),
            CellposeBackend(),
        )
    }


__all__ = [
    "BackendStatus",
    "SegmentationBackend",
    "SegmentationResult",
    "ClassicalBackend",
    "CellposeBackend",
    "LangSAMBackend",
    "MedSAMBackend",
    "MedSAM2Backend",
    "MockBackend",
    "build_default_backends",
]
