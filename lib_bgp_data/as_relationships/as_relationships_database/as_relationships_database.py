#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class AS_Relationship_DB

AS_Relationship_DB can insert as_relationships into a database
"""

from .as_relationships_database_wrapper import AS_Relationships_DB_Wrapper


class AS_Relationship_DB(AS_Relationships_DB_Wrapper):
    """This class inserts as_relationships formatted as dicts into a db"""

    def __init__(self):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """
        pass

    def add_as_relationship(self, row):
        """Inserts a dict of as_relationship into db if it doesn't exist"""

        action = "Updated"
        if not self._as_relationship_exists(row):
            self._insert_as_relationship(row)
            action = "Inserted"
        self.logger.debug("{} as_relationship".format(action))

    def _get_as_relationship_data(self, row):
        """Returns data dict for a sql query from as_relationship dict"""

        customers = row.get("customer_as")
        # Must convert the list of strings to a list of ints
        if customers is not None and not isinstance(customers, list):
            customers = [int(customers)]
        elif customers is not None:
            customers = [int(x) for x in customers]

        data = [row.get("cone_as"),
                customers,
                row.get("provider_as"),
                row.get("peer_as_1"),
                row.get("peer_as_2"),
                row.get("source")
                ]
        # Instead of empty string we want None
        return [x if x != '' else None for x in data]

    def _as_relationship_exists(self, row):
        """Returns True if as_relationship doesn't exist, or False"""

        try:
            # Check to make sure we didn't already insert this as_relationship
            sql = """SELECT * FROM as_relationships
                     WHERE cone_as = %s AND
                     customer_as = %s AND
                     provider_as = %s AND
                     peer_as_1 = %s AND
                     peer_as_2 = %s AND
                     source = %s"""
            self.cursor.execute(sql, self._get_as_relationship_data(row))
            # No results, return false
            results = self.cursor.fetchone()
            self.logger.debug("Selected as_relationship")
            if results is None:
                return False
            else:
                return True
        except Exception as e:
            self.logger.error(
                "Problem selecting as_relationship: {}".format(e))
            raise e

    def _insert_as_relationship(self, row):
        """Inserts as_relationship data into database"""
        try:
            sql = """INSERT INTO as_relationships
                     (cone_as, customer_as, provider_as, peer_as_1,
                     peer_as_2, source)
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            self.cursor.execute(sql, self._get_as_relationship_data(row))
            self.logger.debug("Inserted as_relationship")
        except Exception as e:
            self.logger.error("Problem inserting as_relationship".format(e))
            raise e
