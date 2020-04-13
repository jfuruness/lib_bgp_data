#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class Attack.

This class is used to store information about an attack.

See README for in depth instruction
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Attack:
    def __init__(self, attacker_rows, victim_rows):
        self.attacker_asn = attacker_rows[0][2]
        self.attacker_prefix = attacker_rows[0][0]
        if victim_rows:
            self.victim_asn = victim_rows[0][2]
            self.victim_prefix = victim_rows[0][0]
        else:
            self.victim_asn = None
            self.victim_prefix = None
