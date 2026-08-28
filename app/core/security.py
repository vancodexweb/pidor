from cryptography.fernet import Fernet, InvalidToken


class TokenDecryptionError(Exception):
    """Raised when a stored bot token cannot be decrypted with the current key."""


def encrypt_token(raw_token: str, encryption_key: str) -> str:
    fernet = Fernet(encryption_key.encode())
    return fernet.encrypt(raw_token.encode()).decode()


def decrypt_token(encrypted_token: str, encryption_key: str) -> str:
    fernet = Fernet(encryption_key.encode())
    try:
        return fernet.decrypt(encrypted_token.encode()).decode()
    except InvalidToken as exc:
        raise TokenDecryptionError("Stored token could not be decrypted") from exc


def generate_encryption_key() -> str:
    return Fernet.generate_key().decode()
