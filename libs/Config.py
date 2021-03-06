import yaml


class Config(object):
    def __init__(self):
        with open('etc/config.yml') as yamlfile:
            cfg = yaml.load(yamlfile, Loader=yaml.FullLoader)

        self.database_host = cfg["database"]["host"]
        self.database_port = cfg["database"]["port"]
        self.database_database = cfg["database"]["database"]
        self.database_user = cfg["database"]["user"]
        self.database_password = cfg["database"]["password"]

        self.master_location = cfg["master"]["location"]

        self.ldap_host = cfg["ldap"]["host"]
        self.ldap_port = cfg["ldap"]["port"]
        self.ldap_username = cfg["ldap"]["username"]
        self.ldap_password = cfg["ldap"]["password"]