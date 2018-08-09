#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class Announcements_DB_Wrapper

Announcements_DB_Wrapper has functions that can be called from other
scripts to make the database easier to use
"""


class Announcements_DB_Wrapper:
    """This class contains database wrapper functions

    records, elements, or communities can be selected using this class
    """

    def __init__(self, verbose=False):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """
        pass

    def select_record(self, record_id=None):
        """Returns all records from the database in a list of dictionaries

        If record_id is input then all records with that corresponding id
        are returned. If there are no results an empty list will be returned.
        """

        try:
            if record_id is None:
                self.cursor.execute("SELECT * FROM records;")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM records WHERE record_id = %s"
                self.cursor.execute(sql, [record_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected {} records".format(len(results)))
            return results
        except Exception as e:
            self.logger.error("Problem selecting record(s): {}".format(e))
            raise e

    def select_element(self, element_id=None):
        """Returns all elements from the database in a list of dicts

        If element_id is input then all elements with that corresponding id
        are returned. If there are no results an empty list will be returned.
        """

        try:
            if element_id is None:
                self.cursor.execute("SELECT * FROM elements;")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM elements WHERE element_id = %s;"
                self.cursor.execute(sql, [element_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected {} elements".format(len(results)))
            return results
        except Exception as e:
            self.logger.error("Problem selecting element(s): {}".format(e))
            raise e

    def select_community(self, community_id=None):
        """Returns all communities from the database in a list of dicts

        If community_id is input then all communities with that id
        are returned. If there are no results an empty list will be returned.
        """

        try:
            if community_id is None:
                self.cursor.execute("SELECT * FROM communities")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM communities WHERE community_id = %s"
                self.cursor.execute(sql, [community_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected {} communities".format(len(results)))
            return results
        except Exception as e:
            self.logger.error("Problem selecting element(s): {}".format(e))
            raise e
