#/usr/bin/env python
from _pybgpstream import BGPStream, BGPRecord, BGPElem
import datetime
import calendar
import re

class BGP_Records:

    def __init__(self):
        """
        Initializes a reusable BGPRecord instance

        Input
            self    class object
        Output
            None    NoneType
        """

        self.rec = BGPRecord()

    def get_records(self, start=None, end=None, collector=None,
                    peer_asn=None, prefix=None):
        """
        Uses pybgpstream to get info from BGP records and BGP elems

        Input
            self         class object
            start        datetime.datetime    start time to search
            end          datetime.datetime    emd time to search
            collector    str                  name of the collector ex: rrc11
            peer_asn     str                  number of peer asn ex: 25152
            prefix       str                  prefix, ex: 185.84.166.0/23
        Output
            None    NoneType
        """
        # Note: collector is not manditory, only time
        if None in [start, end]:
            raise Exception("Start, end required")
        if not isinstance(start, datetime.datetime):
            raise Exception("Start is not a datetime object")
        if not isinstance(end, datetime.datetime):
            raise Exception("End is not a datetime object")

        # Create a new bgpstream instance
        stream = BGPStream()

        # Add filters if params exist
        if peer_asn is not None:
            stream.add_filter('peer-asn', peer_asn)
        if prefix is not None:
            stream.add_filter('prefix', prefix)
        if collector is not None:
            stream.add_filter('collector', collector)

        # Time params must be in epoch
        start_epoch = calendar.timegm(start.timetuple())
        end_epoch = calendar.timegm(end.timetuple())
        stream.add_interval_filter(start_epoch, end_epoch)

        # Start the stream
        stream.start()

        information = []
        # Get next record
        while(stream.get_next_record(self.rec)):
            # Print the record information only if it is not a valid record
            information.append(DB_Info(self.rec))
            if self.rec.status != "valid":
                pass
            else:
                elem = self.rec.get_next_elem()
                while(elem):
                    information[-1].add_element(elem)
                    elem = self.rec.get_next_elem()
        return information

class DB_Info:
    def __init__(self, record):
        self.add_record(record)
        self.elements = []

    def add_record(self, record):
        self.record = {"record_project": record.project,
                       "record_collector": record.collector,
                       "record_type": record.type,
                       "record_time": record.time,
                       "record_status": record.status
                      }

    def add_element(self, element):
        element_info = {}
        element_info["element_type"] = element.type
        element_info["element_peer_address"] = element.peer_address
        element_info["element_peer_asn"] = element.peer_asn
        fields = element.fields
        as_path = fields.get("as-path")
        if as_path is not None:
            element_info["as_path"] = [int(x) for x in re.findall('\d+', as_path)]
        element_info["prefix"] = fields.get("prefix")
        element_info["next_hop"] = fields.get("next-hop")
        element_info["communities"] = fields.get("communities")
        self.elements.append(element_info)
#start = datetime.datetime(2015, 8, 1, 8, 20, 11)
#end = start
#records = BGP_Records()
#records.get_records(start, end) 
