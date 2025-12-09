import fcntl, time
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
            value = int(content) if content.isdigit() else -1
            if not (0 <= value <= self.concurrency):
                f.seek(0)
                f.write("0")
                f.truncate()
            fcntl.flock(f, fcntl.LOCK_UN)

    def _get_current_counter(self):
        with open(self.lock_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            content = f.read().strip()
            fcntl.flock(f, fcntl.LOCK_UN)
        return int(content) if content.isdigit() else 0

    def _modify_counter(self, delta: int, block: bool):
        f = open(self.lock_file, "r+")
        try:
            # exclusive lock only during modification
            if block:
                fcntl.flock(f, fcntl.LOCK_EX)
            else:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    f.close()
                    return None, None

            content = f.read().strip()
            old = int(content) if content.isdigit() else 0
            new = max(0, old + delta)

            f.seek(0)
            f.write(str(new))
            f.truncate()

            return old, new
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()

    def acquire_fd(self, block=True):
        while True:
            # quick hint-check
            if self._get_current_counter() >= self.concurrency:
                if not block:
                    return None
                time.sleep(0.05)
                continue

            old, new = self._modify_counter(+1, block)
            if old is None or new is None:  # non-blocking fail
                if not block:
                    return None
                time.sleep(0.05)
                continue

            if new <= self.concurrency:
                logger.debug(f"[Lock Acquired] {new}/{self.concurrency}")
                # return just a dummy object for release() to use
                return True

            # rollback (rare race)
            self._modify_counter(-1, True)

            if not block:
                return None
            time.sleep(0.05)

    def release_fd(self, _):
        old, new = self._modify_counter(-1, True)
        logger.debug(f"[Lock Released] {new}/{self.concurrency}")

    def acquire(self, block=True) -> bool:
        return self.acquire_fd(block) is not None

    def release(self):
        self._modify_counter(-1, True)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = self.acquire_fd(block=True)
            try:
                return func(*args, **kwargs)
            finally:
                self.release_fd(token)

        return wrapper
