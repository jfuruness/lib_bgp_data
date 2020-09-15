#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the rpki_validator_wrapper.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness, Tony Zheng"]
__credits__ = ["Justin Furuness, Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from unittest.mock import Mock, patch
import time
from os import system, path, listdir
import filecmp
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from multiprocessing import Process
import subprocess
from pathlib import Path
import urllib

import pytest
from psutil import process_iter
import pytest
from ..rpki_validator_wrapper import RPKI_Validator_Wrapper
from ...utils import utils

@pytest.mark.rpki_validator
class Test_RPKI_Validator_Wrapper:
    """Tests all local functions within the RPKI_Validator_Wrapper class."""

    @pytest.mark.skip(reason="New hires will work on this")
    path = ('lib_bgp_data.rpki_validator.rpki_validator_wrapper.'          
            'RPKI_Validator_Wrapper.')

    @pytest.fixture
    def wrapper(self, test_table):
        self.test_table = test_table
        return RPKI_Validator_Wrapper(table_input=test_table)

    def test___init__(self):
        """Initializes the RPKI Validator.

        Asserts that if it is not installed that the install script
        gets run.
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_contextmanager(self):
        """Initializes the RPKI Validator and runs context manager

        Test context manager functions. Make sure that it cleans up
        properly. Also make sure that it can start one after the other
        (the second process should obliterate the first). Make sure
        that if the db directories are not owned by root it still works.

        Note that the start_validator test is kind of lumped in here

        Make sure to use a small input file for this.
        """


    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test__kill8080(self):
        """Initializes the RPKI Validator and tests kill8080 function

        Spawns a 8080 process, and runs kill8080 to make sure it dies.
        If wait is true, should ensure that it waits long enough to reclaim
        ports.
        """


        # check port is open in the context manager
        with wrapper as validator:
            validator.load_trust_anchors()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                assert s.connect_ex(('localhost', wrapper.port)) == 0
        
        # and closed outside the context manager
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            assert s.connect_ex(('localhost', wrapper.port)) != 0


    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_load_trust_anchors(self):
        """Initializes the RPKI Validator and tests load_trust_anchors function

        Tests the load_trust_anchors function. For this, run the rpki
        validator and check that the trust anchors
        A: do not load immediatly
        B: That there are five of them
        """

        with wrapper as validator:
            p = Process(target = validator.load_trust_anchors)
            # set this to close child processes
            p.daemon = True
            p.start()
            # finish within 25 minutes
            p.join(1500)
            assert not p.is_alive()

            # closing the multiprocessing
            p.close()
            p.terminate()
            p.join()
            p.clear()

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_make_query(self):
        """Initializes the RPKI Validator and tests make_query function

        For this, run the rpki validator and make some queries to it's
        other API endpoints, ensuring that a proper response is returned.
        """

        with wrapper as validator:
            validator.load_trust_anchors()
            # API call to validate prefix 1.2.0.0/16
            result = validator.make_query('validate/prefix?p=1.2.0.0%2F16')
            print(result)
            assert result == 'OK'

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_get_validity_data(self):
        """Initializes the RPKI Validator and tests get_validity_data function

        Run rpki validator and get validity data. Also ensure that the
        total prefix origin pairs cause an error if > 100000000
        """
        
        wrapper.total_prefix_origin_pairs = 100000001
        with pytest.raises(AssertionError):
            wrapper.get_validity_data()
        
        wrapper.total_prefix_origin_pairs = 3000
        with wrapper as validator:
            validator.load_trust_anchors()
            data = validator.get_validity_data()
        for datum in data:
            assert ['asn', 'prefix', 'validity'] == list(datum.keys())

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_get_validition_status(self):
        """Initializes the RPKI Validator and tests get_validition_status

        Run rpki validator and call this function to ensure it works.
        In addition, send a mock json back, and ensure expected pass
        conditions cause a return of True, and vice versa. Also ensure
        Connection refused errors return False
        """

        path = f'{self.path}make_query'

        with patch(path) as mock_invalid:
            mock_invalid.return_value = [{'completedValidation': False}]
            assert wrapper._get_validation_status() is False


    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_get_validity_dict(self, wrapper):
        """Initializes the RPKI Validator and tests get_validity_dict

        Run rpki validator and get validity data as json. Ensure that
        there are no values that exist that are not in this dict.
        """

        with wrapper as validator:
            validator.load_trust_anchors()
            data = validator.get_validity_data()
            keys = RPKI_Validator_Wrapper.get_validity_dict().keys()
            for datum in data:
                assert datum['validity'] in keys

    @pytest.mark.skip(reason="New hires will work on this")
    def test_rpki_install(self):
        """Initializes the RPKI Validator and installs it

        For this test, delete the installation directory. Then install.
        Make sure that the paths seem correct and that they exist.

        In addition, check the conf folders against hidden conf folder
        in this test directory.
        """

        self.test___init__()

        # db_paths is a list of strings, other 2 are strings
        paths = RPKI_Validator_Wrapper.rpki_db_paths + \
                [RPKI_Validator_Wrapper.rpki_package_path] + \
                [RPKI_Validator_Wrapper.rpki_run_path]

        for p in paths:
            assert path.exists(p)

        # in the hidden .conf folder, the respective modified files
        # are shaved down to just the lines that are changed.
        # check that all of these lines are correctly in the installed files
        test_path = path.dirname(path.realpath(__file__))
        test_path = path.join(test_path, '.conf')

        install_path = path.join(RPKI_Validator_Wrapper.rpki_package_path,
                                'conf')

        f1 = 'application.properties'
        f2 = 'application-defaults.properties'
        for file_name in [f1, f2]:
            with open(path.join(test_path, file_name)) as correct_file,\
                 open(path.join(install_path, file_name)) as install_file:

                installed_file_lines = install_file.readlines()
                for line in correct_file:
                    assert line in installed_file_lines

    @pytest.mark.skip(reason="New hires will work on this")
    def test_rpki_download_validator(self):
        """Tests _download_validator

        For this test, delete the installation directory. Then
        download and move the validator. Assert all files exist
        where they should, and none exist where they should not.
        This includes arins tal.
        """

        assert False

    @pytest.mark.skip(reason="New hires will work on this")
    def test__change_file_hosted_location(self):
        """Tests _change_file_hosted_location

        For this test, delete the installation directory. Then
        download and move the validator. Replace the necessary lines.
        Assert that the old lines are not there and that the new lines are.
        In addition, check that RPKI_File and RPKI_Validator is not in the file
        (at least I don't think that it should be) to check for fstring errors
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    def test__change_server_address(self):
        """Tests _change_server_address

        For this test, delete the installation directory. Then
        download and move the validator. Replace the necessary lines.
        Assert that localhost is no longer in the file.
        In addition, check that RPKI_File and RPKI_Validator is not in the file
        (at least I don't think that it should be) to check for fstring errors
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    def test__config_absolute_paths(self):
        """Tests _change_server_address

        For this test, delete the installation directory. Then
        download and move the validator. Replace the necessary lines.
        Assert that localhost is no longer in the file.
        In addition, check that RPKI_File and RPKI_Validator is not in the file
        (at least I don't think that it should be) to check for fstring errors
        """

        pass
