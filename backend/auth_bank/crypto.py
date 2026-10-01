import os
from cryptography.fernet import Fernet

class CryptoService:
    @staticmethod
    def get_key() -> bytes:
        key = os.getenv("AUTH_BANK_ENCRYPTION_KEY")
        if not key:
            if os.getenv("APP_ENV", "development").lower() == "production":
                raise ValueError("AUTH_BANK_ENCRYPTION_KEY environment variable is required in production")
            print("WARNING: Using default encryption key for development.")
            key = "fK4H3B_2d6Gq8zR1T5wS9YmV7pL0cX4vN8sJ3kF5A_8="
            os.environ["AUTH_BANK_ENCRYPTION_KEY"] = key
        return key.encode()

    @staticmethod
    def encrypt(data: str) -> str:
        f = Fernet(CryptoService.get_key())
        return f.encrypt(data.encode()).decode()

    @staticmethod
    def decrypt(data: str) -> str:
        f = Fernet(CryptoService.get_key())
        return f.decrypt(data.encode()).decode()
