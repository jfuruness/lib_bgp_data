#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the config.py file.
For specifics on each test, see docstrings under each function.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..config import Config


@pytest.mark.database
class Test_Config:
    """Tests all local functions within the Config class."""

    @pytest.mark.skip(reason="New hire work")
    def test_create_config(self):
        """Tests create config function.

        Should delete conf and then create it and make sure it's correct
        Also create it again after t is already created.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_remove_old_config_section(self):
        """Tests removal of old config section.

        Should remove if exists. Check both on existing and non existing key.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_read_config(self):
        """Tests the reading of the config file.

        ints should return as ints. Strings as strings.
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_get_db_creds(self):
        """tests get_db_creds

        Should make sure proper db creds are returned and that none are empty.
        Should try with a new section and make sure it installs it
        should try with error=True on no new section and make sure it errors
        make sure db creds are accurate by logging in with them
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_install(self):
        """Tests install function

        Test install when section already exists (should return db creds)
        test install when no section, should create section and install db
            -make sure this works by logging into the db
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_ram(self):
        """Make sure ram returns properly"""

        pass
    @pytest.mark.skip(reason="New hire work")
    def test_restart_postgres_cmd(self):
        """Tests postgres restart

        Makes sure that the command actually restarts postgres
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_write_to_config(self):
        """Test writing to a config

        Write to a config, check to make sure it's correct.
        """

        pass
