#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a thread-safe abstraction of tdqm.

The purpose of this class is to simplify the use of tdqm
by abstracting away the progress bar and the update of the
progress bar. As a manual tqdm progress bar isn't thread-safe,
used a threading Lock to make it thread-safe.

Design Choices (summarizing from above):
    -Uses a blocking lock.
        -This is fine because there are not many threads running.

Possible Future Extensions:
    -Add test cases
"""


__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

from threading import Lock
from tqdm import tqdm
import os

from .constants import Constants


class MtTqdm:
    """Implement a tqdm progress bar that supports multithreaded
    manual updating. For a more in depth explanation
    see the top of the file.

    Attributes:
        _lock: threading.Lock, A multithreading, blocking lock.
        _pbar: tqdm.tqdm, A manual tqdm progress bar.
        _update_val: float, The value that the pbar should update
            each time an event occurs. The event must be uniform.
    """

    def __init__(self, update_value):
        self._lock = Lock()
        self._pbar = tqdm(total=100)
        self._update_val = update_value

    def update(self):
        """Update the tqdm progress bar. Thread safe."""
        self._lock.acquire()
        if (self._pbar.n + self._update_val) >= self._pbar.total:
            self._pbar.update(self._pbar.total - self._pbar.n)
        else:
            self._pbar.update(self._update_val)
        self._lock.release()

    def close(self):
        """Close the tqdm progress bar."""
        if self._pbar.n < self._pbar.total:
            self._pbar.update(self._pbar.total - self._pbar.n)
        self._pbar.close()
