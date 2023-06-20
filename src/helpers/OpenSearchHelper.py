from Config.Config import G_CONFIG
from opensearchpy import OpenSearch, helpers, Search, MultiSearch, Q, exceptions


class OpenSearchHelper():

    def __init__(self):
        config = G_CONFIG.config['opensearch']
        self.__es = OpenSearch(hosts=[{'host': config['host'], 'port': config['port']}],
                               timeout=30, max_retries=3, retry_on_timeout=True)

    def indices_put_template(self, name, body):
        try:
            return self.__es.indices.put_template(name=name, body=body)
        except exceptions.NotFoundError:
            pass

    def indices_put_mapping(self, index, body):
        try:
            return self.__es.indices.put_mapping(index=index, body=body)
        except:
            pass

    def indices_get_alias(self, alias):
        return self.__es.indices.get_alias(alias)

    def indices_create(self, index, body):
        return self.__es.indices.create(index=index, body=body)

    def indices_exists(self, index):
        return self.__es.indices.exists(index)

    def index(self, index, doc_type, id, body, ignore):
        return self.__es.index(index=index,
                               doc_type=doc_type,
                               id=id,
                               body=body,
                               ignore=ignore)

    def get(self, index, id):
        return self.__es.get(index=index, id=id)

    def mget(self, body):
        return self.__es.mget(body=body)

    def bulk(self, body):
        return helpers.bulk(self.__es, body)

    def search(self, index):
        return Search(using=self.__es, index=index)

    def multi_search(self):
        return MultiSearch(using=self.__es)

    def q(self, name, **params):
        return Q(name, params)

    def put_script(self, index, body):
        return self.__es.put_script(id=index, body=body)
