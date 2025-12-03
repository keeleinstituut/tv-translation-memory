import json

from urllib.error import URLError
import urllib.request
import requests
from Config.Config import G_CONFIG


class BuerokrattAnonymizerClient:
    def __init__(self):
        self.baseurl = G_CONFIG.config['anonymiser']['url']
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