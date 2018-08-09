#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module obtains bgp announcements and formats them for a database"""

from _pybgpstream import BGPStream, BGPRecord
import datetime
import calendar
import re


class BGP_Records:
    """This class uses pybgpstream to collect caida announcements

    Each announcement has a record. If the record is valid, it will
    contain elements. Some elements also have communities. Data on 
    non valid records is not collected.
    """

    def __init__(self, logger, args):
        """Initializes a reusable BGPRecord instance"""

        self.rec = BGPRecord()
        self.logger = logger

    def _input_validation(self, start, end):
        """If start or end is not datetime.datetime, raises exception"""

        try:
            if None in [start, end]:
                raise Exception("Start, end required")
            if not isinstance(start, datetime.datetime):
                raise Exception("Start is not a datetime object")
            if not isinstance(end, datetime.datetime):
                raise Exception("End is not a datetime object")
        except Exception as e:
            self.logger.error(
                "Problem in caida announcements input validation: {}"\
                    .format(e))
            raise e

    def _start_stream(self, **filters):
        """Initializes, starts, and returns bgp stream with filters"""

        # Create a new bgpstream instance
        stream = BGPStream()

        # Add filters if params exist
        for key, value in filters.items():
            if (key in ['peer-asn', 'prefix', 'collector']
                    and value is not None):
                stream.add_filter(key, value)

        # Time params must be in epoch
        start_epoch = calendar.timegm(filters.get('start').timetuple())
        end_epoch = calendar.timegm(filters.get('end').timetuple())
        stream.add_interval_filter(start_epoch, end_epoch)

        # Start the stream
        stream.start()
        self.logger.debug("Started stream for caida announcements")
        return stream

    def get_records(self, start=None, end=None, collector=None,
                    peer_asn=None, prefix=None):
        """Uses pybgpstream to get info from BGP records and BGP elems

        start and end must be datetime.datetime objects and are required.
        No other information is required. This function outputs a list of
        the class DB_Info, which is just a way to format announcements.
        """

        try:
            # Input validation
            self._input_validation(start, end)

            stream = self._start_stream(start, end, collector, peer_asn, prefix)

            information = []

            self.logger.info("Parsing Records Now")
            # Get next record
            while(stream.get_next_record(self.rec)):
                # Creates a new instance of DB_Info with record info
                information.append(DB_Info(self.rec))
                # If record is not valid there is no other info to add, so pass
                if self.rec.status != "valid":
                    pass
                # If record is valid, get all corresponding elements
                else:
                    elem = self.rec.get_next_elem()
                    # While there are elements, add them to the last DB_Info
                    while(elem):
                        information[-1].add_element(elem)
                        elem = self.rec.get_next_elem()
            # Return a list of DB_Info
            return information
        except Exception as e:
            self.logger.critical(
                "Problem in BGP_Records.get_records: {}".format(e))
            raise e


class DB_Info:
    """This formats caida announcements

    Each announcement has a record. If the record is valid, it will
    contain elements. Some elements also have communities. Records and
    elements are stored as dictionaries. Elements are stored as a list.
    """

    def __init__(self, record):
        """Initializes a DB_Info instance with record information"""

        self._add_record(record)
        self.elements = []

    def _add_record(self, record):
        """Formats a record to be added to the DB_Info class as a dict"""

        self.record = {"record_project": record.project,
                       "record_collector": record.collector,
                       "record_type": record.type,
                       "record_time": record.time,
                       "record_status": record.status
                       }

    def add_element(self, element):
        """Formats and adds element to DB_Info as a dict"""

        element_info = {}
        element_info["element_type"] = element.type
        element_info["element_peer_address"] = element.peer_address
        element_info["element_peer_asn"] = element.peer_asn
        fields = element.fields
        as_path = fields.get("as-path")
        if as_path is not None:
            element_info["as_path"] = \
                [int(x) for x in re.findall('\d+', as_path)]
        element_info["prefix"] = fields.get("prefix")
        element_info["next_hop"] = fields.get("next-hop")
        element_info["communities"] = fields.get("communities")
        self.elements.append(element_info)
