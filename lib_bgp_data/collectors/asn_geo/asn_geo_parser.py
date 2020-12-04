#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The ASN_Geo_Parser gets the countries and continents associated with an ASN.
By default, the ASNs from the as_connectivity table (relationships parser)
are used.

The RIPE API is first used to get an IP address associated with the ASN.
This is because MaxMind's API uses IP addresses.
Then MaxMind's GeopIP2 API queries a downloaded binary database for the
country and continent data.
The binary database is used because it's the free option.
Setup is required (explained below) to keep the binary database up-to-date.
Sometimes we can't use MaxMind because RIPE doesn't give an IP for the ASN,
or the IP isn't in the MaxMind database, so BGPView is used as an
alternative.

**************************************************************************
SETUP GUIDE
**************************************************************************
First you will need sign up for an account with MaxMind to use their data:
https://www.maxmind.com/en/geolite2/signup

Then you need to generate a config file on their website and paste it into
/etc/GeoIP.conf
"""

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import os
import json
from time import sleep

import geoip2.database
import requests

from ..relationships import Relationships_Parser
from .tables import ASN_Geo_Table
from ...utils.base_classes import Parser
from ...utils import utils


class ASN_Geo_Parser(Parser):

    mmdb = '/usr/share/GeoIP/GeoLite2-Country.mmdb'

    def _run(self, table="as_connectivity"):
        """Parse the country/continents for as_connectivity by default"""
        rows = []

        self.install()

        with ASN_Geo_Table() as t, requests.Session() as sess,\
            geoip2.database.Reader(self.mmdb) as reader:

            # If as_connectivity doesn't exist, run relationships parser
            sql = ("SELECT * FROM INFORMATION_SCHEMA.TABLES "
                   f"WHERE TABLE_NAME = '{table}'")
            if len(t.execute(sql)) == 0:
                Relationships_Parser().run()

            sql = f"SELECT asn FROM {table}"
            asns = t.execute(sql)

            for _ in asns:
                asn = _['asn']

                # skip if already in the table
                sql = f"SELECT * FROM {t.name} WHERE asn = {asn}"
                if len(t.execute(sql)) == 0:
                    rows.append(self.asn_lookup(asn, sess, reader))

                utils.rows_to_db(rows, self.csv_dir, ASN_Geo_Table)

            db.create_index()

    def asn_lookup(self, asn: int, requests_session=None, mmdb_reader=None):

        assert type(asn) is int, "Not a number"

        if requests_session is None:
            requests_session = requests.Session()

        if mmdb_reader is None:
            mmdb_reader = geoip2.database.Reader(self.mmdb)

        ripe = ('https://stat.ripe.net/data/announced-prefixes/'
                f'data.json?resource=AS{asn}')

        c = 0
        r = requests_session.get(ripe)
        while not r.status_code == requests.codes.ok:
            sleep(10)
            r = requests_session.get(ripe)
            if c > 100:
                print('this really not working')

        if not r.status_code == requests.codes.ok:
            return asn, 'n/a', 'n/a'
                        

        prefixes = r.json()['data']['prefixes']

        r.close()

        # RIPE didn't return prefixes, so try BGPView as a backup
        if not prefixes:
            return self._backup_lookup(asn, requests_session)
        else:
            ip = prefixes[0]['prefix'].split('/')[0]

        try:
            response = mmdb_reader.country(ip)
        except geoip2.errors.AddressNotFoundError:
            return self._backup_lookup(asn, requests_session)

        return asn, response.country.iso_code, response.continent.code

    def _backup_lookup(self, asn, requests_session):
        """Sometimes RIPE doesn't return IP for an ASN, so MaxMind won't work.
        So we'll try BGPView API"""

        # Until new countries get created, we'll use this locally downloaded
        # json of country to continent mappings.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(dir_path, 'continent.json')
        with open(json_path, 'r') as f:
            mapping = json.load(f)

        response = requests_session.get(f'https://api.bgpview.io/asn/{asn}')
        response.raise_for_status()
        try:
            country = response.json()['data']['country_code']
        except KeyError:
            country = None

        response.close()

        # Unfortunately these APIs just are not consistent.
        # Not always going to get a country.
        # Can even get 'EU' as the country.
        try:
            continent = mapping[country] if country else ''
        except KeyError:
            continent = country
        
        return asn, country, continent
        
    def install(self):
        """Installs the GeoIP Update tool (assuming Ubuntu system).
           Also adds a cronjob to keep the database updated."""

        assert os.path.exists('/etc/GeoIP.conf'), "Follow setup guide!"

        if not os.path.exists(self.mmdb):
            cmds = ['add-apt-repository ppa:maxmind/ppa',
                    'apt update',
                    'apt install geoipupdate']

            utils.run_cmds(cmds)

            # MaxMind updates on Tuesdays, so we'll update on Wednesdays.
            utils.add_cronjob('GeoIP_Update', 
                              '0 0 * * 3',
                              '/etc/geoipupdate')
