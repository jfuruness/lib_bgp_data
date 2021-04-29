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

Using the different RIR's APIs is convuluted. They each maintain a different
one. RIPE's database lookup tool says it can lookup across all the IRRs but
when I try, I just get errors. Also to get the ASN, you first need to search
by organisation, then get the organisation id, then perform an inverse search
for ASNs using that organisation id.

The list of CDNs is in cdns.txt. It's a handpicked list. Sometimes companies
aren't very tight on branding and register ASNs under a different name.
For this file, each CDN should be written on its own line.
"""

__authors__ = ["Tony Zheng"]
__credits__ = ["Tony Zheng"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import os

from requests import Session

from ...utils.base_classes import Parser
from ...utils import utils
from .tables import CDN_Whitelist_Table


class CDN_Whitelist_Parser(Parser):
    """Downloads the ASNs of listed CDNs"""

    def _run(self, input_file=None):
        """Downloads ASNs of listed CDNs into the DB"""

        if input_file is None:
            path_here = os.path.dirname(os.path.realpath(__file__))
            input_file = os.path.join(path_here, 'cdns.txt')

        whitelist_rows = []

        api_call_count = 0
        api = 'https://api.hackertarget.com/aslookup/?q='
        err_msg = "Can't look up more than 100 CDNs at a time!"
        with Session() as session:

            cdns = self._get_cdns(input_file)
            assert len(cdns) <= 100, err_msg

            for cdn in self._get_cdns(input_file):
                # Try the request a number of times
                max_tries = 3
                for i in range(max_tries):
                    assert api_call_count < 100, err_msg
                    response = session.get(api + cdn)
                    api_call_count += 1
                    response.raise_for_status()
                    result = response.text
                    response.close()

                    # A good result will have lines that look like:
                    # "132892","CLOUDFLARE Cloudflare, Inc., US"
                    # Anything other than this is an error message

                    if result[0] == '"':

                        # Extract ASN by taking the part before the 1st comma
                        # And removing surrounding quotes
                        for line in result.split('\n'):
                            asn = line.split(',')[0].replace('"', '')
                            whitelist_rows.append([cdn, asn])
                        break
                    else:
                        # Design choice?: Error or insert nulls into db
                        raise RuntimeError((f'Failed to get ASNs for {cdn}'
                                            f' with error msg: {result}'))
                        # Usually rate limit or bad CDN name

            utils.rows_to_db(whitelist_rows, self.csv_dir, CDN_Whitelist_Table)

    def _get_cdns(self, input_file):
        """Gets all CDNs from file (default is cdns.txt in this directory)"""

        with open(input_file, 'r') as f:
            return [cdn.strip() for cdn in f if cdn.strip()]
