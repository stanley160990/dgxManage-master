import requests


class REST(object):
    def __init__(self, args1, args2, args3, args4, args5=""):
        self.args1 = args1
        self.args2 = args2
        self.args3 = args3
        self.args4 = args4
        self.args5 = args5

    def send(self):
        http_method = self.args1
        url = self.args2
        headers = self.args3
        payload = self.args4

        response = requests.request(http_method, url, headers=headers, data=payload)

        return response

    def send_with_files(self):
        http_method = self.args1
        url = self.args2
        headers = self.args3
        payload = self.args4
        files = self.args5

        response = requests.request(http_method, url, headers=headers, data=payload, files=files, stream=True)

        return response
