class Announcements_DB:
    def __init__(self):
        pass
    def insert_announcement_info(self, announcement):
        record_id = self.insert_record(announcement.record)
        for element in announcement.elements:
            self.add_element(element, record_id)

    def insert_record(self, record):
        sql = """INSERT INTO records
                 (record_status, record_type, record_collector, 
                 record_project, record_time) 
                 VALUES (%s, %s, %s, %s, %s) 
                 RETURNING record_id"""
        data = [record.get("record_status"),
                record.get("record_type"),
                record.get("record_collector"),
                record.get("record_project"),
                record.get("record_time")
               ]
        self.cursor.execute(sql, data)
        return self.cursor.fetchone().get("record_id")

    def add_element(self, element, record_id):
        element_id = self.insert_element(element, record_id)
        self.add_community(element.get("communities"), element_id)
    def insert_element(self, element, record_id):
        sql = """INSERT INTO elements 
                 (element_type, element_peer_asn, element_peer_address, 
                 as_path, prefix, next_hop, record_id) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s) 
                 RETURNING element_id"""
        data = [element.get("element_type"),
                element.get("element_peer_asn"),
                element.get("element_peer_address"),
                element.get("as_path"),
                element.get("prefix"),
                element.get("next_hop"),
                record_id
               ]
        self.cursor.execute(sql, data)
        return self.cursor.fetchone().get("element_id")

    def add_community(self, community, element_id):
        if community is not None:
            for info in community:
                self.insert_community(info, element_id)

    def insert_community(self, info, element_id):
        sql = """INSERT INTO communities
                 (asn, value, element_id) 
                 VALUES (%s, %s, %s)"""
        data = [info.get("asn"),
                info.get("value"),
                element_id
               ]
        self.cursor.execute(sql, data)
        return True

    def select_record(self, record_id=None):
        if record_id is None:
            sql = "SELECT * FROM records;"
            self.cursor.execute(sql)
        else:
            sql = "SELECT * FROM records WHERE record_id = %s"
            data = [record_id]
            self.cursor.execute(sql, data)
        return self.cursor.fetchall()

    def select_community(self, community_id=None):
        if community_id is None:
            sql = "SELECT * FROM communities"
            self.cursor.execute(sql)
        else:
            sql = "SELECT * FROM communities WHERE community_id = %s"
            data = [community_id]
            self.cursor.execute(sql, data)
        return self.cursor.fetchall()

    def select_element(self, element_id=None):
        if element_id is None:
            sql = "SELECT * FROM elements;"
            self.cursor.execute(sql)
        else:
            sql = "SELECT * FROM elements WHERE element_id = %s;"
            data = [element_id]
            self.cursor.execute(sql, data)
        return self.cursor.fetchall()
