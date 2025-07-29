"""
Fallback implementation of the ``filelock`` module for environments where
the real third‑party package is unavailable.

This module defines a ``Timeout`` exception and a simple ``FileLock``
context manager that uses an exclusive lock file on disk.  It is not
intended to be a drop‑in replacement for the full ``filelock`` package but
provides the minimal functionality required by the SMITH framework for
serialising access to a shared JSON file during testing.  Because the
tests run sequentially and do not spawn multiple processes, this simple
approach is adequate.
"""
import os
import time
from typing import Optional


class Timeout(Exception):
    """Raised when a lock cannot be acquired within the timeout period."""


class FileLock:
    """
    A lightweight file lock that relies on creating an exclusive lock file.

    The lock attempts to create a file at ``lock_path`` using
    ``os.O_CREAT | os.O_EXCL``.  If the file already exists, acquisition
    blocks until it can either remove the stale file (if the owning process
    released it) or the timeout is reached.  Once acquired, the lock
    maintains the file descriptor so the file remains in existence until
    explicitly released.  On release the file is closed and removed.

    Parameters
    ----------
    lock_path: str
        Path to the lock file.  A ``.lock`` suffix is recommended.
    timeout: float, optional
        Maximum number of seconds to wait for acquisition.  Defaults to 5.
    """

    def __init__(self, lock_path: str, timeout: float = 5.0) -> None:
        self.lock_path: str = lock_path
        self.timeout: float = timeout
        self._fd: Optional[int] = None

    def acquire(self):
        """Attempt to acquire the lock, blocking until success or timeout."""
        start = time.time()
        while True:
            try:
                # Use exclusive creation to ensure only one process can
                # successfully create the lock file.  Keep the descriptor
                # open to prevent premature deletion on some platforms.
                self._fd = os.open(
                    self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR
                )
                break
            except FileExistsError:
                if (time.time() - start) >= self.timeout:
                    raise Timeout(
                        f"Could not acquire lock on {self.lock_path}"
                    )
                time.sleep(0.1)
        return self

    def release(self) -> None:
        """Release the lock by closing and removing the lock file."""
        try:
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
            if os.path.exists(self.lock_path):
                os.remove(self.lock_path)
        except Exception:
            # Suppress exceptions during cleanup to mirror the behaviour of
            # the real filelock library, which does not raise on release.
            pass

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc, tb):
        self.release()