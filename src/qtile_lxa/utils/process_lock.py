import fcntl, re, hashlib
from pathlib import Path
from functools import wraps
from libqtile.log_utils import logger


def safe_filename_hash(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()[:12]


class ProcessLocker:
    def __init__(self, app_name: str, lock_dir: Path = Path("/tmp")):
        self.app_name = safe_filename_hash(app_name)
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def acquire_lock(self):
        """Acquire a lock using a specific lock file."""
        lock_file = self.lock_dir / f"{self.app_name}.lock"
        lock_file.touch(exist_ok=True)

        lock_fd = open(lock_file, "r+")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        except BlockingIOError:
            logger.error(
                f"Process locked: Another instance is running for {lock_file}."
            )
            return None

    def release_lock(self, lock_fd):
        if lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock_fd = self.acquire_lock()
            if not lock_fd:
                return
            try:
                return func(*args, **kwargs)
            finally:
                self.release_lock(lock_fd)

        return wrapper
