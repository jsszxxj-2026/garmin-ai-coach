import importlib


def test_home_summary_endpoint_exists(monkeypatch):
    monkeypatch.setenv('GARMIN_EMAIL', 'test@example.com')
    monkeypatch.setenv('GARMIN_PASSWORD', 'test-password')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')

    config_module = importlib.import_module('src.core.config')
    importlib.reload(config_module)

    module = importlib.import_module('backend.app.main')
    importlib.reload(module)

    assert callable(module.get_home_summary_endpoint)
