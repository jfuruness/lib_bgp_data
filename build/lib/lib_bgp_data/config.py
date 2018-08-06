from configparser import SafeConfigParser as SCP


class Config():
    """interact with config file"""
    def __init__(self, path='/etc/bgp/bgp.conf'):
        self.path = path

    def read_config(self, section, tag, raw=False):
        """Reads the specified section from the configuration file"""
        parser = SCP()
        parser.read(self.path)
        return parser.get(section, tag, raw=raw)

    def get_db_creds(self):
        section = "bgp"
        username = self.read_config(section, "username")
        password = self.read_config(section, "password", raw=True)
        host = self.read_config(section, "host")
        database = self.read_config(section, "database")
        return username, password, host, database

