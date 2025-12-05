import fcntl
from pathlib import Path
from libqtile.log_utils import logger


class ProcessLocker:
    def __init__(self, app_name: str, lock_dir: Path = Path("/tmp")):
        self.app_name = app_name
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def acquire_lock(self):
        """Acquire a lock using a specific lock file."""
        lock_file = self.lock_dir / f"{self.app_name}.lock"
        if not lock_file.exists():
            # Ensure the lock file exists
            open(lock_file, "a").close()

        lock_fd = open(lock_file, "r+")
        try:
            # Acquire an exclusive lock
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        except BlockingIOError:
            logger.error(
                f"Process Locked, Another instance is running for {lock_file}."
            )
            return None

    def release_lock(self, lock_fd):
        """Release the lock."""
        if lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
