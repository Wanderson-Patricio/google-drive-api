import json
from cryptography.fernet import Fernet
from typing import Dict

class CriptDict:
    @staticmethod
    def generate_key():
        return Fernet.generate_key()

    @staticmethod
    def encrypt(obj: Dict[str, str], key: str) -> str:
        f = Fernet(key)
        data = json.dumps(obj).encode('utf-8')
        return f.encrypt(data)
    
    @staticmethod
    def decrypt(s: str, key: str) -> Dict:
        f = Fernet(key)
        data = f.decrypt(s)
        return json.loads(data.decode('utf-8'))