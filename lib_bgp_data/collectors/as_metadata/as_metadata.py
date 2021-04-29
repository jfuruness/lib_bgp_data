#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains a function to get an ASN's country and continent.

The RIPE API is first used to get an IP address associated with the ASN.
Then MaxMind's GeopIP2 API queries a downloaded database for the country
and continent data.

Setup guide:

First you will need sign up for an account with MaxMind to use their data:
https://www.maxmind.com/en/geolite2/signup

Then you need to generate a config file on their website and paste it into
/etc/GeoIP.conf
"""

__authors__ = ["Tony Zheng", "Samarth Kasbawala"]
__credits__ = ["Tony Zheng", "Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import os
import requests

import geoip2.database

from tqdm import tqdm
from .tables import ASN_Metadata_Table
from ...utils import utils
from ...utils.database import Database
from ...utils.base_classes import Parser


class ASN_Lookup(Parser):

    # parser specific paths
    geoip_config_path = "/etc/GeoIP.conf"
    geoip_db = "/usr/share/GeoIP/GeoLite2-City.mmdb"

    def _run(self, asn=None, input_table="top_100_ases"):
        """Takes an ASN or a table containing ASNs as input and stores the
        metadata for each one in a table.
        """

        # Arguments asn and input table are mututally exclusive
        assert not(asn is None and input_table is None), \
               "Enter either specific asn or input table, not neither"
        assert not(asn is not None and input_table is not None), \
               "Enter either specific asn or input table, not both"

        # Check the install
        if not self._check_install():
            self._install()

        # Get the asns
        asns = self._get_asns(asn, input_table)

        # Multiprocessing to speedup
        with utils.Pool(None, 1, "ASN Lookup") as pool:
            asn_metadata = list(tqdm(pool.imap(self._get_row, asns),
                                     unit="asns",
                                     total=len(asns)))

        _csv_dir = os.path.join(self.csv_dir, "asn_metadata.csv")
        utils.rows_to_db([row for row in asn_metadata if row is not None],
                         _csv_dir,
                         ASN_Metadata_Table)

    def _get_asns(self, asn, input_table):
        """Method to get the asns to be looked up in a list format"""

        if asn is not None:
            assert type(asn) is int, "asn kwarg must be an integer"
            asns = [asn]
        else:
            assert type(input_table) is str, "input_table kwarg must be a string"
            with Database() as db:
                sql = f"SELECT asn FROM {input_table};"
                asns = [row['asn'] for row in db.execute(sql)]

        return asns

    def _get_row(self, asn):
        """Returns the row to be inserted for particular asn"""

        try:
            ip = self._get_ip(asn)
            response = self._get_response(ip)
            return self._get_metadata(asn, response)
        except Exception:
            # If metadata for particular asn cannot be found, return None
            # This happens if the asn cannot be found in db or if an
            # ip isn't listed for a certain asn
            return None

    def _get_ip(self, asn):
        """Method to get an ip associated with an ASN"""

        ripe = ('https://stat.ripe.net/data/announced-prefixes/'
                f'data.json?resource=AS{asn}')
        with requests.get(ripe) as r:
            r.raise_for_status()
            ip = r.json()['data']['prefixes'][0]['prefix'].split('/')[0]

        return ip

    def _get_response(self, ip):
        """Method to return geoip2 model (city)"""

        with geoip2.database.Reader(self.geoip_db) as reader:
            response = reader.city(ip)
            reader.close()

        return response

    def _get_metadata(self, asn, response):
        """Formats metadata to be inserted into database"""

        return [asn,
                str(response.traits.network),
                response.continent.code,
                response.country.iso_code,
                response.subdivisions.most_specific.iso_code,
                response.city.name,
                response.location.latitude,
                response.location.longitude]

    def _check_install(self):
        """Method to check the install"""

        # Check config and install
        assert os.path.exists(self.geoip_config_path), \
               ("Follow setup guide! It can be found here: "
                "https://www.maxmind.com/en/geolite2/signup")
        if (not os.path.exists(self.geoip_db) or 
            not os.path.exists("/usr/bin/geoipupdate") or
            not os.path.exists("/etc/cron.d/GeoIP_Update")):
            return False
        
        return True

    def _install(self):
        """Installs the GeoIP Update tool (assuming Ubuntu system).
        Also adds a cronjob to keep the database updated. This cronjob
        runs the GeoIP Update tool on Wednesdays so that the most
        up-to-date databases can be used."""

        cmds = ['add-apt-repository ppa:maxmind/ppa',
                'apt update',
                'apt install geoipupdate',
                'geoipupdate']

        utils.run_cmds(cmds)

        # MaxMind updates on Tuesdays, so we'll update on Wednesdays.
        utils.add_cronjob('GeoIP_Update',
                          '0 0 * * 3',
                          '/etc/geoipupdate')
