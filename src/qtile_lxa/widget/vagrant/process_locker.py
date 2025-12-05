import fcntl
from pathlib import Path
from functools import wraps
from libqtile.log_utils import logger
from .safe_file_name import safe_filename, safe_filename_hash


class ConcurrencyLocker:
    """
    A process-safe concurrency limiter.
    concurrency=1 → exclusive lock
    concurrency=N → allow N parallel holders
    """

    def __init__(
        self, locker_id: str, concurrency: int = 1, lock_dir: Path = Path("/tmp")
    ):
        self.lock_file = (
            lock_dir
            / f"lxa_{safe_filename_hash(locker_id)}_{safe_filename(locker_id)}.lock"
        )
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file.touch(exist_ok=True)
        self.concurrency = concurrency
        self._ensure_counter_valid()

    def _ensure_counter_valid(self):
        """If file content is invalid, reset to 0. Otherwise leave it untouched."""
        with open(self.lock_file, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)

            content = f.read().strip()

            if content.isdigit():
                value = int(content)
                # valid counter: leave it
                if 0 <= value <= self.concurrency:
                    fcntl.flock(f, fcntl.LOCK_UN)
                    return

            # If we reach here → invalid or stale counter
            f.seek(0)
            f.write("0")
            f.truncate()

            fcntl.flock(f, fcntl.LOCK_UN)

            logger.warning(f"[Lock Init] Counter reset (invalid): {self.lock_file}")

    def _modify_counter(self, delta: int, block: bool = False):
        """
        Modify counter safely.
        block=True  → wait until lock free
        block=False → fail immediately if locked
        """
        with open(self.lock_file, "r+") as f:
            if block:
                fcntl.flock(f, fcntl.LOCK_EX)
            else:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return None, None

            # Read current count
            content = f.read().strip()
            count = int(content) if content.isdigit() else 0

            new_count = count + delta

            # Rewrite file
            f.seek(0)
            f.write(str(new_count))
            f.truncate()

            # Unlock
            fcntl.flock(f, fcntl.LOCK_UN)

        return count, new_count

    def acquire(self, block: bool = True):
        """
        block=True  → wait for lock
        block=False → fail fast
        """
        count, new_count = self._modify_counter(+1, block)

        # Failed to lock?
        if count is None or new_count is None:
            return False

        # Exceeds concurrency limit?
        if new_count > self.concurrency:
            self._modify_counter(-1, True)
            logger.debug(
                f"[Lock Reject] {new_count}/{self.concurrency} {self.lock_file}"
            )
            return False

        logger.debug(f"[Lock Acquired] {new_count}/{self.concurrency} {self.lock_file}")
        return True

    def release(self):
        old, new = self._modify_counter(-1, True)
        logger.debug(f"[Lock Released] {new}/{self.concurrency} {self.lock_file}")

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.acquire():
                return None
            try:
                return func(*args, **kwargs)
            finally:
                self.release()

        return wrapper
