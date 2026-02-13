def test_wechat_settings_exist():
    from src.core.config import settings

    assert hasattr(settings, "WECHAT_MINI_APPID")
    assert hasattr(settings, "WECHAT_MINI_SECRET")
    assert hasattr(settings, "WECHAT_SUBSCRIBE_TEMPLATE_ID")
    assert hasattr(settings, "GARMIN_CRED_ENCRYPTION_KEY")
