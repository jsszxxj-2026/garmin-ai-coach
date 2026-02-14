import importlib


def test_poll_home_summary_hook_exists(monkeypatch):
    monkeypatch.setenv('GARMIN_EMAIL', 'test@example.com')
    monkeypatch.setenv('GARMIN_PASSWORD', 'test-password')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')

    config_module = importlib.import_module('src.core.config')
    importlib.reload(config_module)

    module = importlib.import_module('backend.app.jobs.poll_garmin')
    importlib.reload(module)

    assert callable(module.poll_garmin_for_user)
