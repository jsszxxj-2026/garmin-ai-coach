def test_wechat_client_token_cache():
    from backend.app.services.wechat_service import WechatService

    svc = WechatService()
    assert hasattr(svc, "get_access_token")
