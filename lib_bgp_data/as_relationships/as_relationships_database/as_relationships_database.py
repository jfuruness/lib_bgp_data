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
        if row.get("cone_as" is None:
            if row.get("peer_as_1") is not None:
                #insert into peers
                self._insert_peers(row)
            else:
                #insert into customer providers
                self._insert_customer_provider_pair(row)
        self.logger.debug("{} as_relationship".format(action))

    def _insert_peers(self, row):
        """insert peer to peer relationship into db"""
        
        try:
            sql = """INSERT INTO peers
                     (peer_as_1, peer_as_2)
                     VALUES (%s, %s)"""
            data = [row.get("peer_as_1"), row.get("peer_as_2")]
            data = [x if x != '' else None for x in data]
            self.cursor.execute(sql, data)
            self.logger.debug("Inserted as_relationship")
        except Exception as e:
            self.logger.error("Problem inserting as_relationship".format(e))
            raise e

    def _insert_customer_provider(self, row):
        """insert customer provider relationship into db"""

        try:
            sql = """INSERT INTO customer_provider_pairs
                     (cutomer_as, provider_as)
                     VALUES (%s, %s)"""
            data = [row.get("cutomer_as"), row.get("provider_as")]
            data = [x if x != '' else None for x in data]
            self.cursor.execute(sql, data)
            self.logger.debug("Inserted as_relationship")
        except Exception as e:
            self.logger.error("Problem inserting as_relationship".format(e))
            raise e

