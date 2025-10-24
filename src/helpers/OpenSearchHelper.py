from Config.Config import G_CONFIG
from opensearchpy import OpenSearch, helpers, Search, MultiSearch, Q, exceptions


class OpenSearchHelper:

    def __init__(self):
        config = G_CONFIG.config['opensearch']

        def parse_bool(value, default=False):
            if not value:
                return default
            return value.lower() in ['true', '1', 'y', 'yes', 't']

        host = config['host'].replace('OPENSEARCH_HOST', '')
        port = config['port'].replace('OPENSEARCH_PORT', '')
        user = config['user'].replace('OPENSEARCH_USER', '')
        password = config['password'].replace('OPENSEARCH_PASSWORD', '')
        use_ssl = parse_bool(config['use_ssl'].replace('OPENSEARCH_USE_SSL', ''), default=False)
        verify_certs = parse_bool(config['verify_certs'].replace('OPENSEARCH_VERIFY_CERTS', ''), default=True)

        opensearch_options = {
            "hosts": [
                {
                    'host': host,
                    'port': port,
                },
            ],
            "timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True,
            "use_ssl": use_ssl,
            "verify_certs": verify_certs,
            "ssl_show_warn": verify_certs,
            "ssl_assert_hostname": verify_certs,
        }

        if user or password:
            opensearch_options['http_auth'] = (user, password)

        self.es = OpenSearch(**opensearch_options)

    def indices_put_template(self, name, body):
        try:
            return self.es.indices.put_template(name=name, body=body)
        except exceptions.NotFoundError:
            pass

    def indices_put_mapping(self, index, body):
        try:
            return self.es.indices.put_mapping(index=index, body=body)
        except:
            pass

    def indices_get_alias(self, alias):
        return self.es.indices.get_alias(alias)

    def indices_create(self, index, body):
        return self.es.indices.create(index=index, body=body)

    def indices_exists(self, index):
        return self.es.indices.exists(index)

    # def index(self, index, doc_type, id, body, ignore=409):
    def index(self, index, id, body, ignore=409):

        return self.es.index(index=index,
                               id=id,
                               body=body,
                               ignore=ignore)

    def get(self, index, id):
        return self.es.get(index=index, id=id)

    def mget(self, body):
        return self.es.mget(body=body)

    def bulk(self, body):
        return helpers.bulk(self.es, body)

    def search(self, index):
        return Search(using=self.es, index=index)

    def multi_search(self, index=None):
        if index is None:
            return MultiSearch(using=self.es)
        return MultiSearch(using=self.es, index=index)

    def put_script(self, index, body):
        return self.es.put_script(id=index, body=body)
