#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains class Attack.

This class is used to store information about an attack.
Currently this only accounts for hijacks

See README for in depth instruction
"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

class Attack:
    """Attack class that contains information for a victim and an attacker

    Currently this is only used for hijackings"""

    def __init__(self, attacker_rows, victim_rows):
        """rows format is [[prefix, [attacker_asn], attacker_asn, time]]

        this is similar to the mrt announcements format""" 

        self.attacker_asn = attacker_rows[0]["origin"]
        self.attacker_prefix = attacker_rows[0]["prefix"]
        if victim_rows:
            self.victim_asn = victim_rows[0]["origin"]
            self.victim_prefix = victim_rows[0]["prefix"]
        # non competing hijack has no victim
        else:
            self.victim_asn = None
            self.victim_prefix = None
        self.attacker_rows = attacker_rows
        self.victim_rows = victim_rows

    def __repr__(self):
        return (f"Attacker asn: {self.attacker_asn}\n"
                f"Attacker Prefix: {self.attacker_prefix}\n"
                f"Victim asn: {self.victim_asn}\n"
                f"Victim prefix: {self.victim_prefix}\n"
                f"Attacker rows: {self.attacker_rows}\n"
                f"Victim rows: {self.victim_rows}\n")