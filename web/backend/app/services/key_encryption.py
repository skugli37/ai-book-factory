from cryptography.fernet import Fernet # pyre-ignore[21]
import os

# MASTER_KEY should be a 32-byte base64 encoded string
# Generate one with Fernet.generate_key() and store in .env
MASTER_KEY = os.getenv("B4F_MASTER_KEY", Fernet.generate_key().decode())

cipher_suite = Fernet(MASTER_KEY.encode())

class KeyEncryptionService:
    @staticmethod
    def encrypt(key: str) -> str:
        if not key:
            return ""
        return cipher_suite.encrypt(key.encode()).decode()

    @staticmethod
    def decrypt(encrypted_key: str) -> str:
        if not encrypted_key:
            return ""
        try:
            return cipher_suite.decrypt(encrypted_key.encode()).decode()
        except Exception:
            return "ERROR: Could not decrypt key"
