from Config.Config import G_CONFIG
import requests


def scan_file(*files):
    base_uri = G_CONFIG.config['filescan']['api-url']

    def construct_files_body():
        for f in files:
            yield 'FILES', (f.filename, f.stream, f.mimetype)

    body = tuple(construct_files_body())

    url = base_uri + "/v1/scan"
    response = requests.post(url, files=body)

    if response.status_code != 200:
        raise Exception('Invalid response from filescan service: HTTP {}, {}'.format(response.status_code, response.text))

    # Reset filestreams
    for f in files:
        f.stream.seek(0)

    return response.json()['data']['result']


