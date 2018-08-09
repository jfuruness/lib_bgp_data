#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class Announcements_DB

Announcements_DB interacts with the database to insert announcements
collected from caida_announcements
"""

from .announcements_database_wrapper import Announcements_DB_Wrapper


class Announcements_DB(Announcements_DB_Wrapper):
    """This class contains database functions to insert bgp announcements

    Each announcement has a record. If the record is valid, that record will
    have elements. Each element can sometimes have communities.

    Database wrapper functions are found in the announcements_database_wrapper
    """

    def __init__(self):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """
        pass

    def insert_announcement_info(self, announcement):
        """This is the function called to insert a bgp announcement"""

        # Each announcement has a record that must be inserted
        record_id = self._insert_record(announcement.record)
        # Each record has multiple elements that must be inserted
        for element in announcement.elements:
            self._add_element(element, record_id)

    def _add_element(self, element, record_id):
        """Adds an element to the database and it's communities"""

        # Inserts element and returns element_id
        element_id = self._insert_element(element, record_id)
        # Inserts the elements communities
        self._add_community(element.get("communities"), element_id)

    def _add_community(self, community, element_id):
        """Adds info from communities into the database"""

        if community is not None:
            for info in community:
                self._insert_community(info, element_id)

########################
### Insert Functions ###
########################

    def _insert_record(self, record):
        """Inserts a record into db and returns the record_id"""
        
        try:
            sql = """INSERT INTO records
                     (record_status, record_type, record_collector,
                     record_project, record_time)
                     VALUES (%s, %s, %s, %s, %s)
                     RETURNING record_id"""
            data = [record.get("record_status"),
                    record.get("record_type"),
                    record.get("record_collector"),
                    record.get("record_project"),
                    record.get("record_time")
                    ]
            self.cursor.execute(sql, data)
            record_id = self.cursor.fetchone().get("record_id")
            self.logger.debug(
                "Inserted a record with an id of {}".format(record_id))
            return record_id
        except Exception as e:
            self.logger.error("Problem inserting record: {}".format(e))
            raise e

    def _insert_element(self, element, record_id):
        """Inserts an element into the database, returning the element_id"""

        try:
            sql = """INSERT INTO elements
                     (element_type, element_peer_asn, element_peer_address,
                     as_path, prefix, next_hop, record_id)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)
                     RETURNING element_id"""
            data = [element.get("element_type"),
                    element.get("element_peer_asn"),
                    element.get("element_peer_address"),
                    element.get("as_path"),
                    element.get("prefix"),
                    element.get("next_hop"),
                    record_id
                    ]
            self.cursor.execute(sql, data)
            element_id = self.cursor.fetchone().get("element_id")
            self.logger.debug(
                "Inserted an element with an id of {}".format(element_id))
            return element_id
        except Exception as e:
            self.logger.error("Problem inserting record: {}".format(e))
            raise e

    def _insert_community(self, info, element_id):
        """Inserts community info into the database"""

        try:
            sql = """INSERT INTO communities
                     (asn, value, element_id)
                     VALUES (%s, %s, %s)"""
            data = [info.get("asn"),
                    info.get("value"),
                    element_id
                    ]
            self.cursor.execute(sql, data)
            self.logger.debug(
                "Inserted a community, asn: {}, value: {}, element_id: {}"\
                    .format(*data))
        except Exception as e:
            self.logger.error("Problem inserting community: {}".format(e))
            raise e
