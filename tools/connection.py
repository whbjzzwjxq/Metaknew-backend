import redis
from elasticsearch import Elasticsearch
from py2neo import Graph

# postgre
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "metaknew_production",
        "USER": "metaknew",
        "PASSWORD": "12345678",
        "HOST": "101.200.192.71",
        "PORT": "5432",
    }
}

# redis
pool = redis.ConnectionPool(host="101.200.192.71", port=6379, db=1, decode_responses=True)
redis_instance = redis.StrictRedis(connection_pool=pool)

# Neo4j
graph = Graph("bolt://101.200.192.71:7687", Name="neo4j", password="12345678")


# elasticsearch
es_connection = Elasticsearch([{"host": "101.200.192.71", "port": 8013}])
