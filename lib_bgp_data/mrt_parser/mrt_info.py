#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module is for parsing of an mrt file
This code is mostly modified from the mrtparser packages mrt2bgpdump code:
https://github.com/t2mune/mrtparse/blob/master/examples/mrt2bgpdump.py
Credit goes to them, if the documentation for this code is bad, it's because
their documentation is very bad and I still don't know why some of this code
is written the way that it is
Note that error catcher is not called in this code to optimize it best
"""

import copy
from datetime import *
from mrtparse import *

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__Version__ = "0.1.0"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


# I know globals are like so bad, this was from their code, I don't care
# enough to fix it
peer = None


class BgpDump:
    """This class is for turning mrt files into bgpdump data"""

    __slots__ = ['ts', 'peer_ip', 'peer_as', 'nlri', 'as_path', 'next_hop',
                 'rows']

    def __init__(self, rows):
        """Inits BgpDump class"""

        self.nlri = []
        self.rows = rows

    def td_v2(self, m, IPV4, IPV6):
        """This function does a table dump version 2
        This does a table dump version 2 and inserts the information into
        the rows list. If IPV4 IPV4 data will be collected, if IPV6 then that
        data will be collected
        Again, sorry for the bad documentation, a lot is not my code"""

        # this is needed
        global peer
        # ts stands for timestamp
        self.ts = m.ts
        # If these two accepted subtypes
        if ((m.subtype == TD_V2_ST['RIB_IPV4_UNICAST'] and IPV4)
                or (m.subtype == TD_V2_ST['RIB_IPV6_UNICAST'] and IPV6)):
            self.nlri.append('%s/%d' % (m.rib.prefix, m.rib.plen))
            for entry in m.rib.entry:
                self.peer_ip = peer[entry.peer_index].ip
                self.peer_as = peer[entry.peer_index].asn
                self.next_hop = []
                for attr in entry.attr:
                    self._bgp_attr(attr)
                self._print_routes()
        # If it is one of these types but not ipv4 or ipv6 it's fine
        elif (m.subtype == TD_V2_ST['RIB_IPV4_UNICAST']
                or m.subtype == TD_V2_ST['RIB_IPV6_UNICAST']):
            pass
        # Do this for peer index table
        elif m.subtype == TD_V2_ST['PEER_INDEX_TABLE']:
            peer = copy.copy(m.peer.entry)
        # If it's not one of these, the support for those subtypes have been
        # deleted for speed, so it's a problem
        else:
            raise Exception("Not supported subtype")

    def _bgp_attr(self, attr):
        """Function seems to assign attributes to entries?
        Again, their code, not mine"""

        if attr.type == BGP_ATTR_T['NEXT_HOP']:
            self.next_hop.append(attr.next_hop)
        elif attr.type == BGP_ATTR_T['AS_PATH']:
            self.as_path = []
            for seg in attr.as_path:
                if seg['type'] != AS_PATH_SEG_T['AS_SET']:
                    self.as_path += seg['val']
                # Not doing anything with as sets
                else:
                    pass
                    # self.as_path.append('{%s}' % ','.join(seg['val']))
        elif attr.type == BGP_ATTR_T['MP_REACH_NLRI']:
            self.next_hop = attr.mp_reach['next_hop']

    def _print_routes(self):
        """Appends data to the self.rows table"""

        for prefix in self.nlri:
            for next_hop in self.next_hop:
                self.rows.append(
                    [self.peer_as,
                     self.peer_ip,
                     ''.join(["{", ', '.join(self.as_path), "}"]),  # AS Path
                     prefix,
                     next_hop,
                     datetime.utcfromtimestamp(self.ts).strftime('%s')
                     ])


def main(path_to_file, IPV4=True, IPV6=False):
    """Function that gets the data to return for the csv file
    If IPV4 it gets IPV4 data, if IPV6 it gets IPV6 data"""

    rows = []
    # Reader is from mrtparser I think
    for m in Reader(path_to_file):
        m = m.mrt
        if m.err:
            continue
        else:
            m.type == MRT_T['TABLE_DUMP_V2']
            # Writes new rows to rows
            BgpDump(rows).td_v2(m, IPV4, IPV6)
    return rows
