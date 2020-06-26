#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This submodule generates the autonomous system numbers registered to 
companies that serve content delivery networks using Hacker Target's API. 
I have found this to be this API to be the most reliable and 
simplest way to get ASNs for a company.

(Note: The API only allows 100 lookups per day for free.)

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
from .tables import Whitelist_Table

class Whitelist(Parser):
    
    def _run(self):
        whitelist = []

        api = 'https://api.hackertarget.com/aslookup/?q='
        with Session() as session: 

            path_here = os.path.dirname(os.path.realpath(__file__))
            cdn_list_path = path_here + '/cdns.txt'
            with open(cdn_list_path, 'r') as f:
        
                for cdn in f:

                    # in case there's a blank line
                    if not cdn.strip():
                        continue

                    cdn = cdn.strip()
                    response = session.get(api + cdn)
                    response.raise_for_status()

                    for line in response.text.split('\n'):
                        asn = line.split(',')[0].replace('"', '')
                        whitelist.append([cdn, asn])

                    response.close()
        
            utils.rows_to_db(whitelist, self.csv_dir, Whitelist_Table)
 
       
