import fcntl, time, random
from pathlib import Path
from functools import wraps
from libqtile.log_utils import logger
from .safe_file_name import safe_filename, safe_filename_hash


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

    def acquire_fd(self, wait=True):
        while True:
            if self._get_current_counter() >= self.concurrency:
                if not wait:
                    return None
                time.sleep(0.02 + random.random() * 0.03)
                continue

            old, new = self._modify_counter(+1, wait)
            if old is None:  # NB fail
                if not wait:
                    return None
                time.sleep(0.02 + random.random() * 0.03)
                continue

            if new is not None and new <= self.concurrency:
                logger.debug(f"[Lock Acquired] {new}/{self.concurrency}")
                return True

            # rare race → rollback: if someone else incremented after our shared-lock check
            self._modify_counter(-1, True)

            if not wait:
                return None
            time.sleep(0.02 + random.random() * 0.03)

    def release_fd(self, _token):
        old, new = self._modify_counter(-1, True)
        logger.debug(f"[Lock Released] {new}/{self.concurrency}")

    def acquire(self, wait=True) -> bool:
        return self.acquire_fd(wait) is not None

    def release(self):
        self.release_fd(True)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = self.acquire_fd(wait=True)
            try:
                return func(*args, **kwargs)
            finally:
                self.release_fd(token)

        return wrapper
