#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the rpki_validator_wrapper.py file.
For specifics on each test, see docstrings under each function.
"""

import pytest
from ..rpki_validator_wrapper import RPKI_Validator_Wrapper
from ...utils import utils


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

@pytest.mark.rpki_validator
class Test_RPKI_Validator_Wrapper:
    """Tests all local functions within the RPKI_Validator_Wrapper class."""

    @pytest.mark.skip(reason="New hires will work on this")
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

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test__kill8080(self):
        """Initializes the RPKI Validator and tests kill8080 function

        Spawns a 8080 process, and runs kill8080 to make sure it dies.
        If wait is true, should ensure that it waits long enough to reclaim
        ports.
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_load_trust_anchors(self):
        """Initializes the RPKI Validator and tests load_trust_anchors function

        Tests the load_trust_anchors function. For this, run the rpki
        validator and check that the trust anchors
        A: do not load immediatly
        B: That there are five of them
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_make_query(self):
        """Initializes the RPKI Validator and tests make_query function

        For this, run the rpki validator and make some queries to it's
        other API endpoints, ensuring that a proper response is returned.
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_get_validity_data(self):
        """Initializes the RPKI Validator and tests get_validity_data function

        Run rpki validator and get validity data. Also ensure that the
        total prefix origin pairs cause an error if > 100000000
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_get_validition_status(self):
        """Initializes the RPKI Validator and tests get_validition_status

        Run rpki validator and call this function to ensure it works.
        In addition, send a mock json back, and ensure expected pass
        conditions cause a return of True, and vice versa. Also ensure
        Connection refused errors return False
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    @pytest.mark.slow
    def test_get_validity_dict(self):
        """Initializes the RPKI Validator and tests get_validity_dict

        Run rpki validator and get validity data as json. Ensure that
        there are no values that exist that are not in this dict.
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    def test_rpki_install(self):
        """Initializes the RPKI Validator and installs it

        For this test, delete the installation directory. Then install.
        Make sure that the paths seem correct and that they exist.

        In addition, check the conf folders against hidden conf folder
        in this test directory.
        """

        pass

    @pytest.mark.skip(reason="New hires will work on this")
    def test_rpki_download_validator(self):
        """Tests _download_validator

        For this test, delete the installation directory. Then
        download and move the validator. Assert all files exist
        where they should, and none exist where they should not.
        This includes arins tal.
        """

        pass

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
