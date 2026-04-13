from cryptography.fernet import Fernet
from django.conf import settings


class KeyEncryption:
    """Handle encryption/decryption of API keys using Fernet."""

    @staticmethod
    def _get_cipher():
        """Get or create the Fernet cipher."""
        secret_key = getattr(settings, "AI_ENCRYPTION_KEY", None)
        if not secret_key:
            raise ValueError("AI_ENCRYPTION_KEY not configured in settings")
        return Fernet(secret_key.encode() if isinstance(secret_key, str) else secret_key)

    @staticmethod
    def encrypt(plaintext: str) -> bytes:
        """Encrypt an API key."""
        cipher = KeyEncryption._get_cipher()
        return cipher.encrypt(plaintext.encode())

    @staticmethod
    def decrypt(ciphertext: bytes) -> str:
        """Decrypt an API key."""
        cipher = KeyEncryption._get_cipher()
        return cipher.decrypt(ciphertext).decode()
