import time
import fcntl
from pathlib import Path
from functools import wraps
from libqtile.log_utils import logger
from .safe_file_name import safe_filename, safe_filename_hash


class ConcurrencyLocker:
    """
    Best-of-both-worlds concurrency limiter.

    - concurrency = 1 → mutex
    - concurrency = N → allow N parallel holders
    - acquire_fd() → returns FD so caller can release explicitly
    - acquire() → simple boolean return
    - crash-safe / drift-safe
    """

    def __init__(
        self, locker_id: str, concurrency: int = 1, lock_dir: Path = Path("/tmp")
    ):
        self.concurrency = concurrency
        self.lock_file = (
            lock_dir
            / f"lxa_{safe_filename_hash(locker_id)}_{safe_filename(locker_id)}.lock"
        )
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file.touch(exist_ok=True)

        self._ensure_counter_valid()

    def _ensure_counter_valid(self):
        """Ensure stored counter is integer in range."""
        with open(self.lock_file, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)

            content = f.read().strip()
            if content.isdigit():
                value = int(content)
                if 0 <= value <= self.concurrency:
                    fcntl.flock(f, fcntl.LOCK_UN)
                    return

            f.seek(0)
            f.write("0")
            f.truncate()
            fcntl.flock(f, fcntl.LOCK_UN)

            logger.warning(f"[Lock Init] Counter reset: {self.lock_file}")

    # ---------------------------------------------------------
    # READ COUNTER (NO MODIFICATION)
    # ---------------------------------------------------------
    def _get_current_counter(self) -> int:
        """
        Safely read the current concurrency counter using a shared lock.
        """
        with open(self.lock_file, "r") as fd:
            try:
                fcntl.flock(fd, fcntl.LOCK_SH)
                content = fd.read().strip()
                count = int(content) if content.isdigit() else 0
                return count
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)

    # -------------------------------------------------------
    # Low-level atomic counter modification
    # -------------------------------------------------------
    def _modify_counter(self, delta: int, block: bool):
        """
        Atomically modify counter.

        Returns:
            (old_value, new_value, fd)
            If failure → (None, None, None)
        """
        fd = open(self.lock_file, "r+")

        try:
            # Lock
            if block:
                fcntl.flock(fd, fcntl.LOCK_EX)
            else:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    fd.close()
                    return None, None, None

            # Read counter
            content = fd.read().strip()
            old = int(content) if content.isdigit() else 0
            new = old + delta

            # Write back
            fd.seek(0)
            fd.write(str(new))
            fd.truncate()

            # Release lock BEFORE returning FD to caller
            fcntl.flock(fd, fcntl.LOCK_UN)

            return old, new, fd

        except Exception:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception:
                pass
            fd.close()
            raise

    # -------------------------------------------------------
    # Acquire with FD (best of v2)
    # -------------------------------------------------------
    def acquire_fd(self, block: bool = True):
        """
        Acquire lock → returns FD.
        FD is UNLOCKED by the time it's returned (safe for caller).

        Caller must pass FD back to release_fd().
        """
        while True:
            current_counter = self._get_current_counter()
            if current_counter is not None and current_counter < self.concurrency:
                old, new, fd = self._modify_counter(+1, block)

                logger.debug(
                    f"[Lock Acquired] {new}/{self.concurrency} {self.lock_file}"
                )
                return fd
            if not block:
                return None
            else:
                time.sleep(1)
                continue

            # Block=True → loop and retry

    # -------------------------------------------------------
    # Release FD
    # -------------------------------------------------------
    def release_fd(self, fd):
        try:
            # Read current value
            fd.seek(0)
            content = fd.read().strip()
            count = int(content) if content.isdigit() else 1

            new = max(0, count - 1)

            # Write new value
            fd.seek(0)
            fd.write(str(new))
            fd.truncate()

            logger.debug(f"[Lock Released] {new}/{self.concurrency} {self.lock_file}")

        finally:
            fd.close()

    # -------------------------------------------------------
    # High-level acquire() bool API (best of v1)
    # -------------------------------------------------------
    def acquire(self, block: bool = True) -> bool:
        fd = self.acquire_fd(block)
        if fd is None:
            return False
        fd.close()  # user doesn’t manage FD manually
        return True

    # -------------------------------------------------------
    # High-level release() for boolean acquire()
    # -------------------------------------------------------
    def release(self):
        # atomic decrement (no FD needed)
        self._modify_counter(-1, True)

    # -------------------------------------------------------
    # Decorator support (best of v1)
    # -------------------------------------------------------
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
