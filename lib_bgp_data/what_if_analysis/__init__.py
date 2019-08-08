#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class What_If_Analysis

The purpose of this class is to determine the effect that security
policies would have on each AS. This is done through a series of steps.

1. We have hijack tables and the ROV validity table. We first need to
   permute these tables, to get every possible combination of hijack,
   policy, and blocked or not blocked. This is done in the
   split_validitity_table sql queries.
2. We then combine each of these permutations with the output of the
   prefix origin pairs from the extrapolator. Remember, the extrapolator
   has inverse results. In other words, normally the extrapolator
   contains the local RIB for each ASN. Instead, it now contains
   everything BUT the local RIB for each ASN (discluding all prefix
   origin pairs not covered by a ROA). Now, because of this, when we
   combine each permuation of tables from step 1, we are getting all
   the data from that table that the ASN did not keep. Knowing this
   information, we must count the total of things which we did not keep,
   and subtract them from the total of everything in that category. For
   example: when we combine the invalid_asn_blocked_hijacked tables with
   the extrapolation results, we are getting all invalid_asn_blocked_hijacks
   that the ASN did NOT keep in their local RIB. So we must count these
   rows, i.e. the total number of invalid_asn_blocked_hijacked that the
   ASN did not keep, and subtract that number from the total number of
   invalid_asn_blocked_hijacked to get the total number of
   invalid_asn_blocked_hijacked that the AS did keep. This idea can be
   seen in each SQL query in the all_sql_queries. Hard to wrap your head
   around? I feel you. There's no easy way to explain it. Inverting
   the extrapolator results makes this process very complex and hard to
   understand, and I still have trouble thinking about it even though
   I wrote the code.
3. Simply run all of these sql queries to get data.
   Again, apologies for the insufficient explanation. I simply do not
   know how to write about it any better, and whoever modifies this
   code after me will probably only be able to understand it with a
   thorough in person explanation. Good luck.

Design choices (summarizing from above):
    -We permute the hijacks with each policy and blocked or not blocked
     to make the sql queries easier when combining with the extrapolator
     results.
    -We subtract the combination of any hijack table with the
     extrapolation results from the total to get what each AS actually
     had (explained above).
    -We invert extrapolation results to save space and time when doing
     what if analysis queries. This is because each AS keeps almost all
     of the announcements sent out over the internet.
    -If an index is not included it is because it was never used

Possible Future Extensions:
    -Aggregate what if analysis:
        -what if analysis for treating multiple asns as a single AS
    -Add test cases
    -Multithreading
    -Make the sql queries into sql files
"""

from .what_if_analysis import What_If_Analysis

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"
