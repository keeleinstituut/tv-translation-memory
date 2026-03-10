import json

from urllib.error import URLError
import urllib.request
import requests
from Config.Config import G_CONFIG


class BuerokrattAnonymizerClient:
    def __init__(self):
        url = G_CONFIG.config.get('anonymiser', {}).get('url')
        self.baseurl = url if url and url != 'ANONYMISER_URL' else None
        self.timeout = 30
        self.ssl_context = None

    def predict(self, texts, pseudonymize=True, tokenize=True, truecase=True):
        if not self.baseurl:
            return [{'sisendtekst': None, 'anonümiseeritud_tekst': None} for _ in texts]

        url = "{0}/predict".format(self.baseurl)
        data = {
            'texts': texts,
            'pseudonymize': pseudonymize,
            'tokenize': tokenize,
            'truecase': truecase,
        }

        r = requests.post(url, json=data)
        return r.json()