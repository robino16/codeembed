import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from codeembed.locks.base import LockBase
from codeembed.utils.checksum_utils import string_to_sha256

logger = logging.getLogger(__name__)

_LOCKS_DIR = Path(".codeembed/locks")
_LOCK_TTL_SECONDS = 600


class FileLock(LockBase):
    """Cross-process file-level lock stored under .codeembed/locks/."""

    def __init__(self, file_path: str, ttl_seconds: int = _LOCK_TTL_SECONDS) -> None:
        self._file_path = file_path
        self._ttl_seconds = ttl_seconds
        self._secret = str(uuid.uuid4())
        self._lock_path = _LOCKS_DIR / f"{string_to_sha256(file_path)}.lock"

    def try_acquire(self) -> bool:
        _LOCKS_DIR.mkdir(parents=True, exist_ok=True)

        if self._lock_path.exists():
            try:
                with open(self._lock_path) as f:
                    data = json.load(f)
                expires_at = datetime.fromisoformat(data["expires_at"])
                if expires_at > datetime.now(timezone.utc):
                    return False  # Active lock held by another process
            except Exception:
                pass  # Corrupt lock — fall through to steal it

            try:
                self._lock_path.unlink()
            except Exception:
                return False  # Another process deleted/recreated it first

        try:
            fd = os.open(str(self._lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)
                payload = json.dumps(
                    {
                        "pid": os.getpid(),
                        "secret": self._secret,
                        "file_path": self._file_path,
                        "expires_at": expires_at.isoformat(),
                    }
                ).encode()
                os.write(fd, payload)
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            return False  # Lost the creation race to another process

    def release(self) -> None:
        try:
            with open(self._lock_path) as f:
                data = json.load(f)
            if data.get("secret") == self._secret:
                self._lock_path.unlink(missing_ok=True)
        except Exception:
            pass
