#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This submodule generates the autonomous system numbers registered to
companies that serve content delivery networks using Hacker Target's API.
I have found this to be the most reliable and simplest way to get ASNs for a
company.

Notably, they allow 100 lookups per day for free. Getting all the ASNs for one
company counts as one lookup.

There are several tools that a quick google search returns, however most of
them don't return all the ASNs for a company, or some companies don't show up
in search, or can't search for the company by name. I'll list them here:
utratools.com
mxtoolbox.com
dnschecker.org
spyse.com
ipinfo.io

Using the different IRR's APIs is convuluted. They each maintain a different
one. RIPE's database lookup tool says it can lookup across all the IRRs but
when I try, I just get errors. Also to get the ASN, you first need to search
by organisation, then get the organisation id, then perform an inverse search
for ASNs using that organisation id.

The list of CDNs is in cdns.txt. It's a handpicked list. Sometimes companies
aren't very tight on branding and register ASNs under a different name.
"""

__authors__ = ["Tony Zheng"]
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os

from requests import Session

from ..base_classes.parser import Parser
from ..utils import utils
from .tables import CDN_Whitelist_Table


class CDN_Whitelist(Parser):
    """Downloads the ASNs of listed CDNs"""

    def _run(self):
        """Downloads ASNs of listed CDNs into the DB"""

        whitelist = []

        api = 'https://api.hackertarget.com/aslookup/?q='
        with Session() as session:
            for cdn in self._get_cdns():
                # Get ASN data
                response = session.get(api + cdn)
                # Check for errors
                response.raise_for_status()

                # Format data for db insertion
                for line in response.text.split('\n'):
                    asn = line.split(',')[0].replace('"', '')
                    whitelist.append([cdn, asn])

                response.close()

            utils.rows_to_db(whitelist, self.csv_dir, CDN_Whitelist_Table)

    def _get_cdns(self):
        """Gets all CDNs from local file"""

        path_here = os.path.dirname(os.path.realpath(__file__))
        cdn_list_path = path_here + '/cdns.txt'

        with open(cdn_list_path, 'r') as f:
            return [cdn.strip() for cdn in f if cdn.strip()]
