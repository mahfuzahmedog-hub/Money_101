import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.db import get_connection


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


class CredentialVault:
    def __init__(self, passphrase: str, db_path=None):
        salt_path = db_path + ".salt" if db_path else "agent_data.db.salt"
        if os.path.exists(salt_path):
            with open(salt_path, "rb") as f:
                self._salt = f.read()
        else:
            self._salt = os.urandom(16)
            with open(salt_path, "wb") as f:
                f.write(self._salt)
        key = _derive_key(passphrase, self._salt)
        self._fernet = Fernet(key)
        self._db_path = db_path

    def store(self, service: str, username: str, password: str, notes=""):
        enc = self._fernet.encrypt(password.encode()).decode()
        conn = get_connection(self._db_path)
        conn.execute(
            """INSERT OR REPLACE INTO vault (service, username, password_encrypted, created_at, status, notes)
               VALUES (?, ?, ?, datetime('now'), 'active', ?)""",
            (service, username, enc, notes),
        )
        conn.commit()
        conn.close()

    def retrieve(self, service: str):
        conn = get_connection(self._db_path)
        row = conn.execute(
            "SELECT username, password_encrypted FROM vault WHERE service = ?", (service,)
        ).fetchone()
        conn.close()
        if row:
            return row["username"], self._fernet.decrypt(row["password_encrypted"].encode()).decode()
        return None, None
