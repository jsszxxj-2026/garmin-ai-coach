def test_encrypt_roundtrip():
    from backend.app.utils.crypto import encrypt_text, decrypt_text

    plaintext = "secret"
    cipher = encrypt_text(plaintext)
    assert decrypt_text(cipher) == plaintext
