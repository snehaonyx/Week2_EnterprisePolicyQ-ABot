"""Helpers for turning in-memory file bytes into a real path on disk.

Document loaders (e.g. PyPDFLoader) need a filesystem path, not raw
bytes - this bridges Streamlit's in-memory upload object to that
requirement.
"""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def temp_file_from_bytes(data: bytes, suffix: str = "") -> Iterator[Path]:
    """Write `data` to a temp file and yield its path; delete on exit."""
    fd, name = tempfile.mkstemp(suffix=suffix)
    path = Path(name)
    try:
        with open(fd, "wb") as f:
            f.write(data)
        yield path
    finally:
        path.unlink(missing_ok=True)
