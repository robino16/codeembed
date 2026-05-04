import hashlib


def string_to_sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()
