def test_wechat_login_endpoint():
    from backend.app.api.wechat import router

    assert router is not None
