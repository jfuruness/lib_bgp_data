#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the rpki_file.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness, Tony Zheng"]
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os
import gzip
import socket
from time import sleep

import pytest
import requests
from psutil import process_iter
from ..rpki_file import RPKI_File
from ...utils import utils

@pytest.mark.rpki_validator
class Test_RPKI_File:
    """Tests all local functions within the RPKI_File class."""

    def setup(self):
        """Creates a test table, very small, to init the file, and inits"""

        # Here should have a table class imported from another file
        # This table can have very few lines in it, that's totally fine
        # Should have a structure similar to mrt_announcements_table
        # Table should delete everything in it, and fill with data
        pass

    @pytest.mark.skip(reason="new hire will work on this")
    def test___init__(self):
        """Tests the __init__ function

        Create the RPKI file with the test input table and close it"""

        pass

    @pytest.mark.skip(reason="new hire will work on this")
    def test_total_lines(self):
        """Tests the total lines attribute.

        Does this by initing the file instance, and checking
        to make sure total lines is same as entries in db.
        """

        pass

    @pytest.mark.skip(reason="new hire will work on this")
    def test_gzip(self):
        """Tests the gzip function.

        Does this by gzipping the file, then ungzipping to a different
        location and checking that the two are the same.

        Also must assert that the original path is deleted upon gzip"""

    @pytest.mark.skip(reason="new hire will work on this")
    def test_spawn_process(self):
        """Tests the spawn_process function.

        Does this by spawning the file process. Should check that you can
        download the file and that the file is the same as the one
        uploaded.
        """

        pass

    @pytest.mark.skip(reason="new hire will work on this")
    def test_close_process(self):
        """Tests the spawn_process function.

        Does this by spawning the file process. Should check that you can
        download the file and that the file is the same as the one
        uploaded. (Should prob use test_spawn_process for this). Then
        check that you close the file correctly, and nothing is running
        on port 8000.
        """


       
        if not contextmanager:
            self.rpki_file.spawn_process()
            self.rpki_file.close()

        # check port 8000 is closed
        for process in process_iter():
            for connection in process.connections(kind='inet'):
                assert connection.laddr.port != self.rpki_file.port
        # check file was deleted
        assert not os.path.exists(self.gz_path)
    
    @pytest.mark.skip(reason="new hire will work on this")
    def test_contextmanager(self):
        """Tests the context manager functions.

        Basically tests spawn_process and close, but does this using the
        with statement, instead of closing by default.
        """

        with self.rpki_file as rpki_file:
            self.test_spawn_process(True)
        self.test_close_process(True)