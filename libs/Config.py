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
        self.master_docker_sock = cfg["master"]["docker_sock"]
        self.master_url = cfg["master"]["master_url"]
        self.master_obs_url = cfg["master"]["obs_url"]
        self.master_userdir_path = cfg["master"]["userdir_path"]

        self.agent_id_mensin = cfg["agent"]["id_mesin"]
