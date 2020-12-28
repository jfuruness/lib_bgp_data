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

from .rpki import RPKI
from .roa import ROA

from ....collectors.mrt.mrt_metadata.tables import MRT_W_Metadata_Table


class Attack:
    """Attack class that contains information for a victim and an attacker

    Currently this is only used for hijackings"""

    # NOTE: We assume there is a ROA for the prefix. Nothing more.
    default_subprefix = "1.2.3.0/24"
    default_prefix = "1.2.0.0/16"
    default_superprefix = "1.0.0.0/8"

    runnable_attacks = []

    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses

        This is incredibly useful for a few reasons. Mainly, you can
        strictly enforce proper templating with this. And also, you can
        automatically add all of these things to things like argparse
        calls and such. Very powerful tool.
        """

        super().__init_subclass__(**kwargs)
        if hasattr(cls, "attacker_prefixes"):
            cls.runnable_attacks.append(cls)

    def __init__(self, victim, attacker):
        """Inits attack metadata and roas"""

        # Fills RPKI with roa, in separate method for easy inheritance
        self._get_rpki(victim)
        # Victim and attacker ASNs
        self.victim = victim
        self.attacker = attacker
        # Gets announcements
        self._fill_attacker_victim_rows()
        # Adds data for MRT_Metdata table like ids and such
        self._add_mrt_data()
        # Path manipulation attacks are disabled
        # If you ever change this, make sure to check out get_visible_hijacks
        for asn_dict in self.attacker_rows:
            assert asn_dict["origin"] == attacker

    def _get_rpki(self, victim):
        """Returns instance of RPKI"""

        self.rpki = RPKI([ROA(self.default_prefix, victim)])

    def _fill_attacker_victim_rows(self):
        """Gets victim and attacker rows for announcements for db"""

        self.victim_rows = []
        for prefix in self.victim_prefixes:
            # Rows for db are filled with dictionaries of announcements
            self.victim_rows.append({"prefix": prefix})

        self.attacker_rows = []
        for prefix in self.attacker_prefixes:
            # Rows for db are filled with dict of announcements
            self.attacker_rows.append({"prefix": prefix})

    def _add_mrt_data(self):
        """Adds default data to MRT announcements

        for which data is added, see MRT_Metadata_Table
        in mrt parser
        """

        row_lists = [self.victim_rows, self.attacker_rows]
        asns = [self.victim, self.attacker]
        for i, (asn, rows) in enumerate(zip(asns, row_lists)):
            # for each announcement object
            for asn_dict in rows:
                self._add_default_metadata(asn_dict, asn, i)
        self._add_ids()

    def _add_default_metadata(self, asn_dict, asn, _time):
        """Adds as path, origin, time, roa_validity, other defaults"""

        meta = {"as_path": self._get_as_path(asn, _time),
                "origin": asn,
                # 1 if attacker, 0 if victim
                "time": _time,
                "block_id": 0,
                "monitor_asn": 0,
                "roa_validity": self.rpki.check_ann(asn_dict["prefix"], asn)}
        asn_dict.update(meta)

    def _get_as_path(self, asn, _time):
        """_time is 1 if attacker, 0 if victim"""

        return [asn]

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
        """Gets rows for database insertion to the MRT_W_Metadata table"""

        # Flattens the two lists into one list of announcement dicts
        dict_list = []
        for row_list in [self.victim_rows, self.attacker_rows]:
            for row_dict in row_list:
                dict_list.append(row_dict)

        rows = []
        # For each announcement
        for ann in dict_list:
            # Formats row by converting into a list
            # Formats list strings properly
            rows.append([self._format(ann, x)
                         for x in MRT_W_Metadata_Table.columns])
        return rows

    def _format(self, announcement_dict, column):
        """Formats item for db insertion

        Gets item from dictionary. Formats list if nesseccary
        """

        # Format items if nessecary
        cur_item = announcement_dict.get(column)
        if isinstance(cur_item, list):
            cur_item = str(cur_item).replace("[", "{").replace("]", "}")
        return cur_item
