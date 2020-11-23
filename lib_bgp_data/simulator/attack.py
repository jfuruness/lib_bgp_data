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


class RPKI:
    def __init__(self, roas):
        self.roas = roas

    def check_ann(self, prefix, origin):
        """Checks announcement validity. Returns worst validity found

        NOTE: if you end up doing this with lots of announcements,
        This should probably be done in SQL
        """

        worst_validity = ROA_Validity.UNKNOWN
        prefix = IPNetwork(prefix)
        for roa in self.roas:
            validity = roa.check_validity(prefix, origin)
            # If valid, return
            if validity == ROA_Validity.VALID:
                return validity
            # Continue looking for worst validity possible
            else:
                if worst_validity.value > validity.value:
                    worst_validity = validity

        return worst_validity

class ROA:
    def __init__(self, prefix: IPNetwork, origin: int):
        self.prefix = IPNetwork(prefix)
        self.origin = origin
        self.max_len = self.prefix.prefixlen

    def check_validity(prefix: IPNetwork, origin: int):
        assert isinstance(prefix, IPNetwork), "Convert to IPNetwork"
        if prefix in self.prefix:
            length = True if prefix.prefix_len <= self.max_len else False
            correct_origin = True if origin == self.origin else False
            if length and correct_origin:
                return ROA_Validity.VALID
            elif not length and not correct_origin:
                return ROA_Validity.INVALID_BY_ALL
            elif not length:
                return ROA_Validity.INVALID_BY_LENGTH
            else:
                return ROA_Validity.INVALID_BY_ASN
        else:
            return ROA_Validity.UNKNOWN

class Attack:
    """Attack class that contains information for a victim and an attacker

    Currently this is only used for hijackings"""

    # NOTE: We assume there is a ROA for the prefix. Nothing more.
    default_subprefix = "1.2.3.0/24"
    default_prefix = "1.2.0.0/16"
    default_superprefix = "1.0.0.0/8"


    def __init__(self, victim, attacker):

        self._get_rpki(victim)
        self.victim = victim
        self.attacker = attacker
        self._fill_attacker_victim_rows()
        self._add_mrt_data()

    def _get_rpki(self, victim):
        self.rpki = [ROA(self.default_prefix, victim)]

    def fill_attacker_victim_rows(self):
        self.victim_rows = []
        for prefix in self.victim_prefixes:
            self.victim_rows.append({"prefix": prefix})

        self.attacker_rows = []
        for prefix in self.attacker_prefixes:
            self.attacker_rows.append({"prefix": prefix})

    def _add_mrt_data(self):
        row_lists = [self.victim_rows, self.attacker_rows]
        asns = [self.victim, self.attacker]
        for i, asn, rows in enumerate(zip(asns, row_lists))::
            for asn_dict in rows:
                self._add_default_metadata(asn_dict, asn, i)
        self._add_ids()

    def _add_default_metadata(self, asn_dict, asn, _time):
        """Adds as path and origin"""
        meta = {"as_path": [asn],
                "origin": asn,
                # 1 if attacker, 0 if victim
                "time": _time,
                "block_id": 0,
                "monitor_asn": 0
                "roa_validity": self.rpki.check_ann(asn_dict["prefix"], asn)}
        asn_dict.update(metadata)

    def _add_ids(self):
        """Adds prefix ID, origin ID, prefix origin ID

        The reason we do this here instead of SQL like in MRT_Metadata
        is for speed, since typical case is 2-3 announcements and must be
        run thousands of times
        """

        rows = self.attacker_rows + self.victim_rows

        # Prefix ID
        prefixes = {}
        prefix_counter = 0
        # Origin ID
        origins = {}
        origin_counter = 0
        # Prefix Origins ID
        prefix_origins = {}
        prefix_origins_counter = 0

        # For each row, try to access the attr
        # If you cannot access the attr, set it equal to counter
        # Save to hashmap and incriment by 1
        # Could've shortened it, but this is more readable imo
        for asn_dict in rows:
            # Prefix ID
            try:
                asn_dict["prefix_id"] = prefixes[asn_dict["prefix"]]
            except KeyError:
                prefixes[asn_dict["prefix"]] = prefix_counter
                prefix_counter += 1
                asn_dict["prefix_id"] = prefixes[asn_dict["prefix"]]
            asn_dict["block_prefix_id"] = asn_dict["prefix_id"]
            # Origin ID
            try:
                asn_dict["origin_id"] = origins[asn_dict["origin"]]
            except KeyError:
                origins[asn_dict["origin"]] = origin_counter
                origin_counter += 1
                asn_dict["origin_id"] = origins[asn_dict["origin"]]

            # Prefix Origin ID
            try:
                pair = (asn_dict["prefix"], asn_dict["origin"],)
                asn_dict["prefix_origin_id"] = prefix_origins[pair]
            except KeyError:
                prefix_origins[pair] = prefix_origins_counter
                prefix_origins_counter += 1
                asn_dict["prefix_origin_id"] = prefix_origins[pair]

    @property
    def db_rows(self):
        dict_list = []
        for row_list in [self.victim_rows, self.attacker_rows]:
            for row_dict in row_list:
                dict_list.append(row_dict)

        rows = []
        for ann in dict_list:
            row = []
            for col in MRT_W_Metadata_Table.columns:
                cur_item = ann.get(col)
                if isinstance(cur_item, list):
                    cur_item = str(cur_item).replace("[", "{").replace("]", "}")
                row.append(cur_item)
            rows.append(row)
        return rows

class Subprefix_Hijack(Attack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_subprefix]
    victim_prefixes = [Attack.default_prefix]


class Prefix_Hijack(Attack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix]
    victim_prefixes = [Attack.default_prefix]

class Prefix_Superprefix_Hijack(Attack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix, Attack.default_superprefix]
    victim_prefixes = [Attack.default_prefix]

class Unannounced_Hijack(Attack):
    """Should be inherited, unnanounced attacks"""

    victim_prefixes = []

class Unannounced_Prefix_Hijack(Unannounced_Hijack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix]


class Unannounced_Subprefix_Hijack(Unannounced_Hijack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix, Attack.default_subprefix]

class Unnannounced_Prefix_Superprefix_Hijack(Unannounced_Hijack):
    """Hijack where there is a ROA for default_prefix"""

    attacker_prefixes = [Attack.default_prefix, Attack.default_superprefix]
