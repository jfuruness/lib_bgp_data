import psycopg2
from psycopg2.extras import RealDictCursor

class Database(AS_Relationship_DB, BGPStream_DB, Announcements_DB):
    """Interact with the database to populate them"""
    def __init__(self, verbose=False):
        """Create a new connection with the databse"""
        self.verbose = verbose
        self.config = Config()
        self.conn, self.cursor = self._connect()
        self.conn.autocommit = True

    def _connect(self):
        """Connects to db"""
        username, password, host, database = self.config.get_db_creds()
        try:
            conn = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    database=database,
                                    cursor_factory=RealDictCursor)
            if self.verbose:
                print("Database Connected")
            return conn, conn.cursor()
        except Exception as e:
            raise ('Postgres connection failure: {0}'.format(e))

