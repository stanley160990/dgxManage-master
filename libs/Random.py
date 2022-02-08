from socket import socket


class Rand_socket(object):
    def __init__(self, args1):
        self.args1 = args1

    def random(self):
        with socket() as s:
            s.bind(('',0))
            free_socket = s.getsockname()[1]

        return free_socket