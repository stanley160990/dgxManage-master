import psycopg2
import docker

class Psql(object):
    def __init__(self, args1, args2, args3, args4, args5):
        self.args1 = args1
        self.args2 = args2
        self.args3 = args3
        self.args4 = args4
        self.args5 = args5

    def connect(self):
        host = self.args1
        port = self.args2
        database = self.args3
        username = self.args4
        password = self.args5

        connection = psycopg2.connect(host=host, port=int(port), database=database, user=username,
                                      password=password)
        cursor = connection.cursor()

        return connection, cursor

    def connect_pool(self):
        host = self.args1
        port = self.args2
        database = self.args3
        username = self.args4
        password = self.args5

        postgreSQL_pool = psycopg2.pool.ThreadedConnectionPool(1, 200, user=username,
                                                               password=password,
                                                               host=host,
                                                               port=port,
                                                               database=database)
        return postgreSQL_pool
    
class Docker(object):
    def __init__(self, args1):
        self.args1 = args1
    
    def connect(self):
        sock_file = self.args1

        client = docker.DockerClient(base_url=sock_file)
        

        return client