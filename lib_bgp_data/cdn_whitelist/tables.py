from ..database import Generic_Table


class Whitelist_Table(Generic_Table):
    name = 'asn_whitelist'

    def _create_tables(self):
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS asn_whitelist (
                 name varchar (200),
                 asn bigint
                 );"""
        self.cursor.execute(sql)
