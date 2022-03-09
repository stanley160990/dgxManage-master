import psycopg2
# import docker
from ldap3 import Server, Connection, ALL

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
    
class Ldap(object):
    def __init__(self, args1, args2, args3, args4):
        self.args1 = args1
        self.args2 = args2
        self.args3 = args3
        self.args4 = args4

    def connect(self):
        host = self.args1
        port = self.args2
        username = self.args3
        password = self.args4

        server = Server(host + ":" + str(port), get_info=ALL)
        conn = Connection(server, username, password, auto_bind=True)

        return conn