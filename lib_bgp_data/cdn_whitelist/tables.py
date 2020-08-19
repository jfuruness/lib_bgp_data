from ..database import Generic_Table


class Whitelist_Table(Generic_Table):

    name = 'cdn_whitelist'

    columns = ['cdn', 'asn']

    def _create_tables(self):
        sql = """CREATE UNLOGGED TABLE IF NOT EXISTS cdn_whitelist (
                 cdn varchar (200),
                 asn bigint
                 );"""
        self.cursor.execute(sql)
