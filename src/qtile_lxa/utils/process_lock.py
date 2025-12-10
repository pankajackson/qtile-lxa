from functools import wraps
import random, time, fcntl
from pathlib import Path
from libqtile.log_utils import logger
from qtile_lxa.utils.safe_filename import safe_filename, safe_filename_hash


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


class ConcurrencyLocker:
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
        with open(self.lock_file, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read().strip()
            val = int(content) if content.isdigit() else -1
            if not (0 <= val <= self.concurrency):
                f.seek(0)
                f.write("0")
                f.truncate()
            fcntl.flock(f, fcntl.LOCK_UN)

    def _get_current_counter(self):
        with open(self.lock_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            content = f.read().strip()
            fcntl.flock(f, fcntl.LOCK_UN)

        val = int(content) if content.isdigit() else 0
        return max(0, min(val, self.concurrency))

    def _modify_counter(self, delta: int, wait: bool):
        f = open(self.lock_file, "r+")
        try:
            if wait:
                fcntl.flock(f, fcntl.LOCK_EX)
            else:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    f.close()
                    return None, None

            content = f.read().strip()
            old = int(content) if content.isdigit() else 0
            new = max(0, min(old + delta, self.concurrency))

            f.seek(0)
            f.write(str(new))
            f.truncate()

            return old, new
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            finally:
                f.close()

    def acquire(self, wait=True):
        while True:
            if self._get_current_counter() >= self.concurrency:
                if not wait:
                    return None
                time.sleep(0.02 + random.random() * 0.03)
                continue

            old, new = self._modify_counter(+1, wait)
            if old is None:  # NB-lock failed
                if not wait:
                    return None
                time.sleep(0.02 + random.random() * 0.03)
                continue

            if old < self.concurrency:
                logger.debug(f"[Lock Acquired] {new}/{self.concurrency}")
                return True

            # rare race → rollback: if someone else incremented after our shared-lock check
            self._modify_counter(-1, True)

            if not wait:
                return None
            time.sleep(0.02 + random.random() * 0.03)

    def release(self):
        old, new = self._modify_counter(-1, True)
        logger.debug(f"[Lock Released] {new}/{self.concurrency}")

    def __call__(self, func):
        return self._wrap(func, wait=True)

    def no_wait(self, func):
        return self._wrap(func, wait=False)

    def _wrap(self, func, wait: bool):
        @wraps(func)
        def wrapper(*a, **kw):
            lock = self.acquire(wait=wait)
            if lock is None:
                return None
            try:
                return func(*a, **kw)
            finally:
                self.release()

        return wrapper
