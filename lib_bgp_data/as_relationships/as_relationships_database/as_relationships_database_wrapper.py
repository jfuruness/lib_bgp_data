#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class Announcements_DB_Wrapper

Announcements_DB_Wrapper has functions that can be called from other
scripts to make the database easier to use
"""

class AS_Relationships_DB_Wrapper:
    """This class contains database wrapper functions

    as_relationships can be selected using this class
    """

    def __init__(self, verbose=False):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """
        pass


    def select_relationship(self, relationships_id=None):
        """Returns all as_relationships from the database in a list of dicts

        If relationship_id is input, then all as_relationships with that
        as_relationship_id are returned. If no results, then an empty list
        will be returned.
        """

        try:        
            if relationships_id is None:
                self.cursor.execute("SELECT * FROM as_relationships")
                results = self.cursor.fetchall()
            else:
                sql = "SELECT * FROM as_relationships WHERE relationships_id = %s"
                self.cursor.execute(sql, [relationships_id])
                results = self.cursor.fetchone()
            self.logger.debug("Selected as_relationship")
            return results
        except Exception as e:
            self.logger.error("Problem in select_relationship: {}".format(e))
            raise e
