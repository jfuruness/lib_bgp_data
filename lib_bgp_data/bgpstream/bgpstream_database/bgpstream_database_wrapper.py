#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class BGPStream_DB_Wrapper

BGPStream_DB_Wrapper has functions that can be called from other
scripts to make the database easier to use
"""


class BGPStream_DB_Wrapper:
    """This class contains database wrapper functions

    leaks, hijacks, or outages can be selected using this class
    """

    def __init__(self):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """

        pass


    def select_hijack(self, hijack_id=None):
        """Returns all hijacks from the database in a list of dictionaries

        If hijack_id is input then all hijacks with that corresponding id
        are returned. If there are no results an empty list will be returned.
        """

        try:
            if hijack_id is None:
                self.cursor.execute("SELECT * FROM hijack;")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM hijack WHERE hijack_id = %s"
                self.cursor.execute(sql, [hijack_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected a hijack event")
            return results
        except Exception as e:
            self.logger.error(
                "Problem selecting hijack event: {}".format(e))
            raise e

    def select_leak(self, leak_id=None):
        """Returns all leaks from the database in a list of dictionaries

        If leak_id is input then all leaks with that corresponding id
        are returned. If there are no results an empty list will be returned.
        """

        try:
            if leak_id is None:
                self.cursor.execute("SELECT * FROM leak;")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM leak WHERE leak_id = %s"
                self.cursor.execute(sql, [leak_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected a leak event")
            return results
        except Exception as e:
            self.logger.error("Problem selecting a leak event: {}".format(e))
            raise e

    def select_outage(self, outage_id=None):
        """Returns all outages from the database in a list of dictionaries

        If outage_id is input then all outages with that corresponding id
        are returned. If there are no results an empty list will be returned.
        """

        try:
            if outage_id is None:
                self.cursor.execute("SELECT * FROM outage;")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM outage WHERE outage_id = %s"
                self.cursor.execute(sql, [outage_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected an outage event")
            return results
        except Exception as e:
            self.logger.error(
                "Problem selecting an outage event: {}".format(e))
            raise e
