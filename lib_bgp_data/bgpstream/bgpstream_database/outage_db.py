#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Outage_DB

Outage_DB has database functionality for bgpstream events
It can select, insert, or update outage events
"""

from .helper import format_error


class Outage_DB:
    """This class has database functionality for bgpstream events

    It can select or add outage events
    """

    def __init__(self):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """

        pass

    def add_outage_event(self, event):
        """If event doesn't exist inserts it, else updates it"""

        try:
            outage_id = self._select_outage(event.get("event_number"))
            data = self.get_outage_data(event, outage_id)
            if outage_id is None:
                self._insert_outage(event)
            else:
                self._update_outage(event, outage_id)
        except Exception as e:
            self.logger.error("Problem adding outage event: {}".format(e))
            format_error(locals(), e)

    def _select_outage(self, event_number):
        """Returns outage id based on event_number, or None"""

        sql = "SELECT * FROM outage WHERE event_number = %s"
        self.cursor.execute(sql, [event_number])
        result = self.cursor.fetchone()
        self.logger.debug("Retrieved outage id")
        if result is None:
            return None
        else:
            return result.get("outage_id")

    def _insert_outage(self, event):
        """Inserts outage event"""

        sql = """INSERT INTO outage
              (AS_name, AS_number, country, end_time, event_number,
              event_type, number_prefixes_affected,
              percent_prefixes_affected, start_time, url)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              """
        self.cursor.execute(sql, self.get_outage_data(event))
        self.logger.debug("Inserted outage")

    def _update_outage(self, event, leak_id):
        """Updates outage event"""

        sql = """UPDATE outage SET
              AS_name = %s,
              AS_number = %s,
              country = %s,
              end_time = %s,
              event_number = %s,
              event_type = %s,
              number_prefixes_affected = %s,
              percent_prefixes_affected = %s,
              start_time = %s,
              url = %s
              WHERE outage_id = %s
              """
        self.cursor.execute(sql, self.get_outage_data(event), leak_id)
        self.logger.debug("Updated outage")

    def _get_outage_data(self, event, outage_id=None):
        """Returns a list of data from an event"""

        data = [event.get("AS_name"),
                event.get("AS_number"),
                event.get("country"),
                event.get("end_time"),
                event.get("event_number"),
                event.get("event_type"),
                event.get("number_of_prefixes_affected"),
                event.get("percent_of_prefixes_affected"),
                event.get("start_time"),
                event.get("url")
                ]
        if outage_id is not None:
            data.append(outage_id)
        # We don't want empty strings we want None
        return [x if x != '' else None for x in data]
