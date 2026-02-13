def test_chat_service_reply():
    from backend.app.services.chat_service import ChatService

    svc = ChatService()
    assert hasattr(svc, "reply")
