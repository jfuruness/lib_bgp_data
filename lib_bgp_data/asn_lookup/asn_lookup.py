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

import os

import geoip2.database
import requests
from ..utils import utils

__author__ = "Tony Zheng"
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def asn_lookup(asn: int) -> dict:

    assert type(asn) is int, "Not a number"

    db = '/usr/share/GeoIP/GeoLite2-Country.mmdb'

    assert os.path.exists('/etc/GeoIP.conf'), "Follow setup guide!"

    if not os.path.exists(db):
        install()

    ripe = ('https://stat.ripe.net/data/announced-prefixes/',
            f'data.json?resource=AS{asn}')

    r = requests.get(ripe)
    r.raise_for_status()
    ip = r.json()['data']['prefixes'][0]['prefix'].split('/')[0]
    r.close()

    reader = geoip2.database.Reader(db)

    response = reader.country(ip)

    reader.close()

    return response.country.iso_code, response.continent.code


def install():
    """Installs the GeoIP Update tool (assuming Ubuntu system).
       Also adds a cronjob to keep the database updated."""

    cmds = ['add-apt-repository ppa:maxmind/ppa',
            'apt update',
            'apt install geoipupdate']

    utils.run_cmds(cmds)

    # MaxMind updates on Tuesdays, so we'll update on Wednesdays.
    utils.add_cronjob('GeoIP_Update', 
                      '0 0 * * 3',
                      '/etc/geoipupdate')
