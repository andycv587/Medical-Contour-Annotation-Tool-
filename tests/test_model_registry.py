from segmentation.model_registry import load_model_registry, registry_status_by_backend, validate_model_registry


def test_model_registry_template_loads_as_unconfigured():
    entries = load_model_registry("configs/models.example.yaml")
    assert entries
    assert {entry.backend for entry in entries} >= {"mock", "classical", "langsam", "medsam", "medsam2", "cellpose", "microsam"}
    assert all(not entry.is_configured() for entry in entries if entry.backend not in {"mock", "classical"})


def test_model_registry_template_validates_without_fake_checkpoints():
    summary = validate_model_registry("configs/models.example.yaml")
    assert summary["model_count"] >= 7
    assert summary["configured_count"] == 2
    assert summary["errors"] == []


def test_registry_status_by_backend_reports_not_configured():
    status = registry_status_by_backend("configs/models.example.yaml")
    assert status["langsam"]["status"] == "NOT_CONFIGURED"
    assert status["mock"]["status"] == "CONFIGURED"
