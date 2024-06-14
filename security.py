import os
from cryptography.fernet import Fernet

def get_secure_api_key():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise EnvironmentError("ENCRYPTION_KEY not found in environment variables.")
    cipher_suite = Fernet(key)
    encrypted_api_key = os.getenv("ENCRYPTED_TAVILY_API_KEY")
    if not encrypted_api_key:
        raise EnvironmentError("ENCRYPTED_TAVILY_API_KEY not found in environment variables.")
    return cipher_suite.decrypt(encrypted_api_key.encode()).decode()