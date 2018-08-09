#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Hijack_DB

Hijack_DB has database functionality for bgpstream events
It can select, insert, or update hijack events
"""

from .helper import format_error


class Hijack_DB:
    """This class has database functionality for bgpstream events

    It can select or add hijack events
    """

    def __init__(self):
        """This function should never be called

        The funcs in this class are meant to be added to a Database class
        """

        pass


    def add_hijack_event(self, event):
        """If event doesn't exist inserts it, else updates it"""

        try:
            hijack_id = self._get_hijack_id(event.get("event_number"))
            if hijack_id is None:
                self._insert_hijack(event)
            else:
                self._update_hijack(event, hijack_id)
        except Exception as e:
            self.logger.error(
                "Problem adding hijack event: {}".format(e))
            format_error(locals(), e)

    def _get_hijack_id(self, event_number):
        """Returns hijack id based on event_number, or None"""

        sql = "SELECT * FROM hijack WHERE event_number = %s"
        self.cursor.execute(sql, [event_number])
        result = self.cursor.fetchone()
        self.logger.debug("Retrieved hijack id")
        if result is None:
            return None
        else:
            return result.get("hijack_id")

    def _insert_hijack(self, event):
        """Inserts hijack event"""

        sql = """INSERT INTO hijack
              (country, detected_as_path, detected_by_bgpmon_peers,
              detected_origin_name, detected_origin_number, end_time,
              event_number, event_type, expected_origin_name,
              expected_origin_number, expected_prefix, more_specific_prefix,
              start_time, url)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              """
        self.cursor.execute(sql, self._get_hijack_data(event))
        self.logger.debug("Inserted hijack")

    def _update_hijack(self, event, hijack_id):
        """Updates hijack event"""

        sql = """UPDATE hijack SET
              country = %s,
              detected_as_path = %s,
              detected_by_bgpmon_peers = %s,
              detected_origin_name = %s,
              detected_origin_number = %s,
              end_time = %s,
              event_number = %s,
              event_type = %s,
              expected_origin_name = %s,
              expected_origin_number = %s,
              expected_prefix = %s,
              more_specific_prefix = %s,
              start_time = %s,
              url = %s
              WHERE hijack_id = %s
              """
        self.cursor.execute(sql, self._get_hijack_data(event, hijack_id))
        self.logger.debug("Updated hijack")

    def _get_hijack_data(self, event, hijack_id=None):
        """Returns a list of data from an event"""

        data = [event.get("country"),
                event.get("detected_as_path"),
                event.get("detected_by_bgpmon_peers"),
                event.get("detected_origin_name"),
                event.get("detected_origin_number"),
                event.get("end_time"),
                event.get("event_number"),
                event.get("event_type"),
                event.get("expected_origin_name"),
                event.get("expected_origin_number"),
                event.get("expected_prefix"),
                event.get("more_specific_prefix"),
                event.get("start_time"),
                event.get("url")
                ]
        if hijack_id is not None:
            data.append(hijack_id)
        # We don't want empty strings we want None
        return [x if x != '' else None for x in data]
