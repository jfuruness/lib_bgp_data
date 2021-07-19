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
import configparser
import psycopg2

from ..config import Config
from ..config import set_global_section_header


@pytest.mark.database
class Test_Config:
    """Tests all local functions within the Config class."""

    def test_create_config(self):
        """Tests create config function.

        Should delete conf and then create it and make sure it's correct
        Also create it again after t is already created.
        """
        tags = [['host', ''], ['database', ''], ['password', ''],
                ['user', ''], ['restart_postgres_cmd', '']]
        conf = Config('test')
        for tag in tags:
            tag[1] = conf._read_config('test', tag[0])
        conf.create_config(tags[2][1])
        for tag in tags:
            assert conf._read_config('test', tag[0]) == tag[1]

    def test_remove_old_config_section(self):
        """Tests removal of old config section.

        Should remove if exists. Check both on existing and non existing key.
        """
        conf = Config('test')
        pswd = conf._read_config('test', 'password')
        conf._remove_old_config_section('test')
        with pytest.raises(configparser.NoSectionError):
            conf._read_config('test', 'host')
        conf.create_config(pswd)
        self.test_create_config()

    def test_read_config(self):
        """Tests the reading of the config file.

        ints should return as ints. Strings as strings.
        """
        tags = [('host', str), ('database', str), ('password', str),
                ('user', str), ('ram', int), ('restart_postgres_cmd', str)]
        conf = Config('test')
        for tag in tags:
            read = conf._read_config('test', tag[0])
            assert type(read) == tag[1]

    @pytest.mark.creds
    def test_get_db_creds(self):
        """tests get_db_creds

        Should make sure proper db creds are returned and that none are empty.
        Should try with a new section and make sure it installs it
        should try with error=True on no new section and make sure it errors
        make sure db creds are accurate by logging in with them
        """
        conf = Config('test')
        creds = conf.get_db_creds()
        assert creds is not None
        conf = Config('new_test')
        with pytest.raises(TypeError):
            conf.get_db_creds(error=True)
        creds = conf.get_db_creds()
        print(creds)
        conn = psycopg2.connect(**creds)
        conn.close()
        conf._remove_old_config_section('new_test')

    def test_install(self):
        """Tests install function

        Test install when section already exists (should return db creds)
        test install when no section, should create section and install db
            -make sure this works by logging into the db
        """

        conf = Config('test')
        creds = conf.get_db_creds()
        assert conf.install() == creds
        conf = Config('new_test')
        creds = conf.install()
        conn = psycopg2.connect(**creds)
        conn.close()
        conf._remove_old_config_section('new_test')

    def test_ram(self):
        """Make sure ram returns properly"""
        conf = Config('test')
        ram = conf.ram
        assert type(ram) == int
        assert ram > 0

    @pytest.mark.xfail(reason="skipping, may issues with other's work")
    def test_restart_postgres_cmd(self):
        """Tests postgres restart

        Makes sure that the command actually restarts postgres
        """

        x = 1/0

    def test_write_to_config(self):
        """Test writing to a config

        Write to a config, check to make sure it's correct.
        """
        conf = Config('test')
        conf._write_to_config('test', 'test_subsection', 'test string')
        written = conf._read_config('test', 'test_subsection')
        assert written == 'test string'
        self.test_remove_old_config_section()

    def test_set_global_section_header(self):
        """Test the set global section header function

        Test that the section is set to test"""
        conf = Config('test')
        assert set_global_section_header() == 'test'
