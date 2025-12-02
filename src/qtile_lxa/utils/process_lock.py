import fcntl, re
from pathlib import Path
from functools import wraps
from libqtile.log_utils import logger


def safe_filename(name: str) -> str:
    if "/" in name or "\\" in name:
        raise ValueError(f"Invalid lock name '{name}': path separators not allowed.")
    return re.sub(r"[^A-Za-z0-9_\-]", "_", name)


class ProcessLocker:
    def __init__(self, app_name: str, lock_dir: Path = Path("/tmp")):
        self.app_name = safe_filename(app_name)
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


def process_locker(app_name: str):
    """Decorator factory for locking functions."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            locker = ProcessLocker(app_name)
            lock_fd = locker.acquire_lock()

            if not lock_fd:
                return  # locked → skip execution

            try:
                return func(*args, **kwargs)
            finally:
                locker.release_lock(lock_fd)

        return wrapper

    return decorator
