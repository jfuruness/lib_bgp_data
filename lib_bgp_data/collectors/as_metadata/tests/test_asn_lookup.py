#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""This file contains tests for the asn_lookup.py file.
For speciifics on each test, see the docstrings under each function.
"""


__author__ = "Samarth Kasbawala"
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import os
import pytest
import socket
import geoip2


from unittest.mock import Mock, patch
from ..tables import ASN_Metadata_Table
from ..asn_lookup import ASN_Lookup
from ...roas.roas_parser import ROAs_Parser
from ...roas.tables import ROAs_Table
from ....utils import utils
from ....utils.database import Database


@pytest.mark.asn_lookup
class Test_ASN_Lookup:
    """Tests all functions in the ASN_Lookup class"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Parser setup before every test"""

        self.test_asn = 1
        self.parser = ASN_Lookup()

    def test__install(self):
        """Tests the _install function"""

        # If the db exists, delete it
        if os.path.exists(self.parser.geoip_db):
            utils.run_cmds(f"rm {self.parser.geoip_db}")
        assert not os.path.exists(self.parser.geoip_db)

        # Uninstall geoipupdate
        try:
            utils.run_cmds("apt-get remove geoipupdate -y")
        except Exception as e:
            # If it's not installed, don't do anything
            pass

        assert not os.path.exists("/usr/bin/geoipupdate")

        # Install geoipupdate and ensure the db is installed
        self.parser._install()
        assert os.path.exists(self.parser.geoip_db)
        assert os.path.exists("/usr/bin/geoipupdate")
        assert os.path.exists("/etc/cron.d/GeoIP_Update")

    def test__get_ip(self):
        """Test getting an ip given an asn using ripe api"""

        ip = self.parser._get_ip(self.test_asn)
        assert (self._is_ipv4(ip) or self._is_ipv6(ip))

    def test__get_response(self):
        """Test getting a response from the geoip city database
        using the api"""

        ip = self.parser._get_ip(self.test_asn)
        response = self.parser._get_response(ip)

        assert response is not None
        assert type(response) is geoip2.models.City

    def test__get_metadata(self):
        """Tests that a list is returned containing the metadata for the
        particular asn"""

        ip = self.parser._get_ip(self.test_asn)
        response = self.parser._get_response(ip)
        metadata = self.parser._get_metadata(self.test_asn, response)

        assert type(metadata) is list
        assert len(metadata) == 8

    def test__get_row(self):
        """Test that a list is returned containing the contents we will
        insert in the database. If we pass an invalid argument, the method
        should return None"""

        row = self.parser._get_row("invalid input")
        assert row is None

        row = self.parser._get_row(self.test_asn)
        assert type(row) is list
        assert len(row) is 8

    def test__run_single_asn(self):
        """Tests the _run function on a singular asn input"""
        
        self.parser._run(asn=self.test_asn, input_table=None)

        with ASN_Metadata_Table() as table:
            assert table.get_count() == 1

    def test__run_tabular_input(self):
        """Tests the _run function on tabular input"""

        # Run a parser so we can test tabular input
        ROAs_Parser().run()

        # Get top 100 ases, don't want this test to be too long
        with ROAs_Table() as roas_table:
            sql = f"""CREATE UNLOGGED TABLE IF NOT EXISTS first_100_ases
                   AS SELECT * FROM {roas_table.name} LIMIT 100;
                   """
            roas_table.execute(sql)

        self.parser._run(asn=None, input_table="first_100_ases")

        # We should be able to get metadata for at least 1 asn
        with ASN_Metadata_Table() as table:
            assert table.get_count() > 0

    def test__run_invalid_kwargs(self):
        """Tests the _run function when invalid kwargs are passed"""

        with pytest.raises(AssertionError):
            self.parser._run(asn=None, input_table=None)
            self.parser._run(asn=self.test_asn, input_table="test")
            self.parser._run(asn=1, input_table=None)
            self.parser._run(asn=None, input_table=1)

    def _is_ipv4(self, ip):
        """Utility function to tell if ip is ipv4"""

        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def _is_ipv6(self, ip):
        """Utility function to tell if ip is ipv6"""

        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False

