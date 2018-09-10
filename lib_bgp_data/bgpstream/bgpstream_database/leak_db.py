#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Leak_DB

Leak_DB has database functionality for bgpstream events
It can select, insert, or update leak events
"""

from .helper import format_error


class Leak_DB:
    """This class has database functionality for bgpstream events

    It can select or add leak events
    """

    def __init__(self):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """

        pass


    def add_leak_event(self, event):
        """If event doesn't exist, inserts it, else updates it"""

        try:
            leak_id = self._get_leak_id(event.get("event_number"))
            if leak_id is None:
                self._insert_leak_event(event)
            else:
                self._update_leak_event(event, leak_id)
        except Exception as e:
            self.logger.error("Problem adding leak_event: {}".format(e))
            format_error(locals(), e)

    def _get_leak_id(self, event_number):
        """Returns leak_id based on event_number, or None"""

        sql = "SELECT * FROM leak WHERE event_number = %s"
        self.cursor.execute(sql, [event_number])
        result = self.cursor.fetchone()
        self.logger.debug("retrieved leak_id")
        if result is None:
            return None
        else:
            return result.get("leak_id")

    def _insert_leak_event(self, event):
        """Inserts leak event"""

        sql = """INSERT INTO leak
              (country, detected_by_bgpmon_peers, end_time, event_number,
              event_type, example_as_path, leaked_prefix, leaked_to_name,
              leaked_to_number, leaker_as_name, leaker_as_number,
              origin_as_name, origin_as_number, start_time, url) VALUES
              (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              """
        self.cursor.execute(sql, self.get_leak_data(event))
        self.logger.debug("Inserted Leak event")

    def _update_leak_event(self, event, leak_id):
        """Updates leak event"""

        sql = """UPDATE leak SET
              country = %s,
              detected_by_bgpmon_peers = %s,
              end_time = %s,
              event_number = %s,
              event_type = %s,
              example_as_path = %s,
              leaked_prefix = %s,
              leaked_to_name = %s,
              leaked_to_number = %s,
              leaker_as_name = %s,
              leaker_as_number = %s,
              origin_as_name = %s,
              origin_as_number = %s,
              start_time = %s,
              url = %s
              WHERE leak_id = %s
              """
        self.cursor.execute(sql, self.get_leak_data(event, leak_id))
        self.logger.debug("Updated leak event")

    def _get_leak_data(self, event, leak_id=None):
        """Returns a list of data from a leak event"""

        data = [event.get("country"),
                event.get("detected_by_bgpmon_peers"),
                event.get("end_time"),
                event.get("event_number"),
                event.get("event_type"),
                event.get("example_as_path"),
                event.get("leaked_prefix"),
                event.get("leaked_to_name"),
                [int(x) for x in event.get("leaked_to_number")],
                event.get("leaker_as_name"),
                event.get("leaker_as_number"),
                event.get("origin_as_name"),
                event.get("origin_as_number"),
                event.get("start_time"),
                event.get("url")
                ]
        if leak_id is not None:
            data.append(leak_id)
        # We don't want empty strings, we want None
        return [x if x != '' else None for x in data]
