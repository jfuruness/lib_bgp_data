import pprint

class BGPStream_DB:
    def __init__(self):
        pass
    def sanitize_data(self, data):
        return [x if x != '' else None for x in data]

    def print_error(self, err_info):
        for key, val in err_info.items():
            if key == 'sql':
                pass
            elif key == 'self':
                pass
            elif isinstance(val, dict) or isinstance(val, list):
                print(key)
                pprint.pprint(val)
            else:
                print(key)
                print(val)

    def add_leak_event(self, event):
        try:
            sql = "SELECT * FROM leak WHERE event_number = %s"
            data = [event.get("event_number")]
            self.cursor.execute(sql, data)
            results = self.cursor.fetchall() 
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
            if len(results) == 0:
                sql = """INSERT INTO leak 
                         (country, detected_by_bgpmon_peers, end_time, 
                         event_number, event_type, example_as_path, 
                         leaked_prefix, leaked_to_name, leaked_to_number, 
                         leaker_as_name, leaker_as_number, origin_as_name, 
                         origin_as_number, start_time, url)  
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                         %s, %s, %s)"""
                action = "inserted"
            else:
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
                         WHERE leak_id = %s"""
                data.append(results[0].get("leak_id"))
                action = "updated"
            self.cursor.execute(sql, self.sanitize_data(data))
            if self.verbose:
                print("{} leak".format(action))
        except Exception as e:
            self.print_error(locals())

    def add_outage_event(self, event):
        try:
            sql = "SELECT * FROM outage WHERE event_number = %s"
            data = [event.get("event_number")]
            self.cursor.execute(sql, data)
            results = self.cursor.fetchall()
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
            if len(results) == 0:
                sql = """INSERT INTO outage 
                         (AS_name, AS_number, country, end_time, event_number, 
                         event_type, number_prefixes_affected, 
                         percent_prefixes_affected, start_time, url)  
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                action = "inserted"
            else:
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
                         WHERE outage_id = %s"""
                data.append(results[0].get("outage_id"))
                action = "updated"
            self.cursor.execute(sql, self.sanitize_data(data))
            if self.verbose:
                print("{} outage".format(action))
        except Exception as e:
            self.print_error(locals())

    def add_hijack_event(self, event):
        try:
            sql = "SELECT * FROM hijack WHERE event_number = %s"
            data = [event.get("event_number")]
            self.cursor.execute(sql, data)
            results = self.cursor.fetchall()
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
            if len(results) == 0:
                sql = """INSERT INTO hijack 
                         (country, detected_as_path, detected_by_bgpmon_peers, 
                         detected_origin_name, detected_origin_number, 
                         end_time, event_number, event_type, 
                         expected_origin_name, expected_origin_number, 
                         expected_prefix, more_specific_prefix, start_time, url) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                         %s, %s)"""
                action = "inserted"
            else:
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
                         WHERE hijack_id = %s"""
                data.append(results[0].get("hijack_id"))
                action = "updated"
            self.cursor.execute(sql, self.sanitize_data(data))
            if self.verbose:
                print("{} hijack".format(action))
        except Exception as e:
            self.print_error(locals())    
