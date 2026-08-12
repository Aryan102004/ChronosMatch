"""
ChronosMatch shared memory management.
"""

import mmap
import os


class SharedMemory:
    """Manage the mmap-backed shared memory region."""

    def __init__(self, path: str, size: int):
        self.path = path
        self.size = size

        self._file = None
        self._mmap = None

    def create(self):
        """Create a new shared memory file."""

        self._file = open(self.path, "w+b")

        self._file.truncate(self.size)

        self._mmap = mmap.mmap(
            self._file.fileno(),
            self.size,
            access=mmap.ACCESS_WRITE,
        )

        return self._mmap

    def open(self):
        """Open an existing shared memory file."""

        if not os.path.exists(self.path):
            raise FileNotFoundError(
                f"Shared memory file not found: {self.path}"
            )

        self._file = open(self.path, "r+b")

        self._mmap = mmap.mmap(
            self._file.fileno(),
            self.size,
            access=mmap.ACCESS_WRITE,
        )

        return self._mmap

    @property
    def mmap(self):
        """Return the mmap object."""

        if self._mmap is None:
            raise RuntimeError("Shared memory has not been opened.")

        return self._mmap

    def flush(self):
        """Flush changes to the mapped file."""

        if self._mmap is not None:
            self._mmap.flush()

    def close(self):
        """Close mmap and underlying file."""

        if self._mmap is not None:
            self._mmap.close()
            self._mmap = None

        if self._file is not None:
            self._file.close()
            self._file = None