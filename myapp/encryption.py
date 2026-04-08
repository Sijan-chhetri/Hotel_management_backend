import base64
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _get_fernet() -> Fernet:
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", None)
    if not key:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class EncryptionService:
    """Thin Fernet wrapper for encrypting credential fields at rest."""

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string. Returns base64-encoded ciphertext."""
        if not plaintext:
            return ""
        f = _get_fernet()
        return f.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string. Raises InvalidToken if tampered."""
        if not ciphertext:
            return ""
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()


# Module-level singleton
encryption_service = EncryptionService()
