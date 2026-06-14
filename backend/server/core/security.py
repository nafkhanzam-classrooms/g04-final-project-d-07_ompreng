import hashlib
import hmac
import os
import secrets

ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"

CLIENT_ROLES = {ROLE_STUDENT, ROLE_TEACHER}
STAFF_ROLES = {ROLE_ADMIN, ROLE_TEACHER}

HASH_NAME = "pbkdf2_sha256"
ITERATIONS = 10 # Reduced iterations for better performance in testing/demo environment (But 600k for production ideally :D)
SALT_BYTES = 16

def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        ITERATIONS,
    ).hex()
    return f"{HASH_NAME}${ITERATIONS}${salt}${digest}"

def is_password_hash(value: str) -> bool:
    parts = str(value or "").split("$")
    return len(parts) == 4 and parts[0] == HASH_NAME

def verify_password(password: str, stored_password: str) -> bool:
    if not is_password_hash(stored_password):
        return False

    _, iterations, salt, expected = stored_password.split("$", 3)
    try:
        iteration_count = int(iterations)
    except ValueError:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        iteration_count,
    ).hex()
    return hmac.compare_digest(actual, expected)
