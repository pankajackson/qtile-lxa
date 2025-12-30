import os
import tempfile
from pathlib import Path
from typing import Union
import json

# Supported content types for convenience
AtomicContent = Union[str, bytes, dict, list]


def atomic_write_content(
    path: Path,
    content: AtomicContent,
    *,
    indent: int = 4,
    encoding: str = "utf-8",
):
    """
    Atomically write content to a file.

    Supports:
    - str → text file
    - bytes → binary file
    - dict/list → JSON file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    try:
        # Determine mode and encoding
        if isinstance(content, bytes):
            mode = "wb"
            enc = None
        elif isinstance(content, str):
            mode = "w"
            enc = encoding
        elif isinstance(content, (dict, list)):
            mode = "w"
            enc = encoding
        else:
            raise TypeError(f"Unsupported content type: {type(content)!r}")

        with os.fdopen(tmp_fd, mode, encoding=enc) as f:
            # Write content
            if isinstance(content, (dict, list)):
                json.dump(content, f, indent=indent)
            else:
                f.write(content)

            # Flush to disk
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace
        os.replace(tmp_path, path)

        # Ensure directory metadata is flushed
        dir_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    finally:
        # Cleanup temp file if something failed before replace
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
