import hashlib
import secrets
from hmac import compare_digest

PASSWORD_ITERATIONS = 210_000
SALT_BYTES = 16


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    password_salt = salt if salt is not None else secrets.token_bytes(SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt,
        PASSWORD_ITERATIONS,
    )
    return f"{password_salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, expected_hash_hex = password_hash.split(":", maxsplit=1)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False

    actual_hash = hash_password(password, salt=salt).split(":", maxsplit=1)[1]
    return compare_digest(actual_hash, expected_hash_hex)
