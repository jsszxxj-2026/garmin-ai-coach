import importlib


def test_should_generate_ai_brief_requires_gemini_key(monkeypatch):
    monkeypatch.setenv('GARMIN_EMAIL', 'test@example.com')
    monkeypatch.setenv('GARMIN_PASSWORD', 'test-password')
    monkeypatch.setenv('GEMINI_API_KEY', '')

    config_module = importlib.import_module('src.core.config')
    importlib.reload(config_module)

    service_module = importlib.import_module('backend.app.services.home_summary_service')
    importlib.reload(service_module)

    class DummyGemini:
        pass

    svc = service_module.HomeSummaryService(gemini=DummyGemini())
    assert svc.should_generate_ai_brief() is False
