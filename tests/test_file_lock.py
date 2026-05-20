import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from codeembed.locks import file_lock as fl_module
from codeembed.locks.file_lock import FileLock
from codeembed.utils.checksum_utils import string_to_sha256


@pytest.fixture(autouse=True)
def locks_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(fl_module, "_LOCKS_DIR", tmp_path)
    return tmp_path


def _lock_path(locks_dir: Path, file_path: str) -> Path:
    return locks_dir / f"{string_to_sha256(file_path)}.lock"


def test_acquire_succeeds(locks_dir: Path) -> None:
    lock = FileLock("a.py")
    assert lock.try_acquire() is True
    assert _lock_path(locks_dir, "a.py").exists()


def test_second_acquire_returns_false() -> None:
    FileLock("a.py").try_acquire()
    assert FileLock("a.py").try_acquire() is False


def test_release_allows_reacquire() -> None:
    lock = FileLock("a.py")
    lock.try_acquire()
    lock.release()
    assert FileLock("a.py").try_acquire() is True


def test_expired_lock_is_stolen(locks_dir: Path) -> None:
    path = _lock_path(locks_dir, "a.py")
    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    path.write_text(json.dumps({"pid": 0, "secret": "old", "file_path": "a.py", "expires_at": expired.isoformat()}))

    assert FileLock("a.py").try_acquire() is True


def test_corrupt_lock_is_stolen(locks_dir: Path) -> None:
    _lock_path(locks_dir, "a.py").write_text("not json at all")
    assert FileLock("a.py").try_acquire() is True
