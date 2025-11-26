import json

from urllib.error import URLError
import urllib.request
import requests


class BuerokrattAnonymizerClient:
    def __init__(self):
        self.baseurl = 'http://host.docker.internal:7001'
        self.timeout = 30
        self.ssl_context = None

    def predict(self, texts, pseudonymize=True, tokenize=True, truecase=True):
        url = "{0}/predict".format(self.baseurl)
        data = {
            'texts': texts,
            'pseudonymize': pseudonymize,
            'tokenize': tokenize,
            'truecase': truecase,
        }

        r = requests.post(url, json=data)
        return r.json()