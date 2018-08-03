class Parser:
    def __init__(self):
        self.database = Database()
        self.bgpstream_parser = BGPStream_Website_Parser()
        self.announcements_parser = BGP_Records()
        self.as_relationships_parser = Caida_AS_Relationships_Parser()

    def run_bgpstream_parser(self):
        "parses bgpstream.com and inserts into the database"
        events = self.bgpstream_parser.parallel_parse()
        for event in events:
            if event.get("event_type")=='BGP Leak':
                self.database.add_leak_event(event)
            elif event.get("event_type")=='Outage':
                self.database.add_outage_event(event)
            elif event.get("event_type")=='Possible Hijack':
                self.database.add_hijack_event(event)

    def run_as_relationship_parser(self):
        self.as_relationships_parser.download_files()
        self.as_relationships_parser.unzip_files()
        lines = self.as_relationships_parser.parse_files()
        total_lines = len(lines)
        for i in range(total_lines):
            self.database.add_as_relationship(lines[i])
            print("{}/{} relationships resolved".format(i, total_lines))
        self.as_relationships_parser.clean_up()

    def run_as_announcements_parser(self):
        start = datetime.datetime(2015, 8, 1, 8, 20, 11)
        end = start
        announcements = self.announcements_parser.get_records(start, end)
        for announcement in announcements:
            self.database.insert_announcement_info(announcement)

