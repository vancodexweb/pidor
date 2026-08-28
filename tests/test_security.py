import pytest

from app.core.security import TokenDecryptionError, decrypt_token, encrypt_token, generate_encryption_key


def test_encrypt_decrypt_round_trip():
    key = generate_encryption_key()
    token = "123456789:AAExampleTokenFromBotFather0000000"

    encrypted = encrypt_token(token, key)

    assert encrypted != token
    assert decrypt_token(encrypted, key) == token


def test_decrypt_fails_with_wrong_key():
    key_a = generate_encryption_key()
    key_b = generate_encryption_key()
    encrypted = encrypt_token("some-token", key_a)

    with pytest.raises(TokenDecryptionError):
        decrypt_token(encrypted, key_b)


def test_generated_keys_are_unique():
    assert generate_encryption_key() != generate_encryption_key()
