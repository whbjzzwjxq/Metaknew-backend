import os
import redis
from elasticsearch import Elasticsearch
from py2neo import Graph

gateway = os.getenv('GATEWAY', '127.0.0.1')
# postgre
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "metaknew_production",
        "USER": "metaknew",
        "PASSWORD": "12345678",
        "HOST": gateway,
        "PORT": "5432",
    }
}

# redis
pool = redis.ConnectionPool(host=gateway, port=6379, db=1, decode_responses=True)
redis_instance = redis.StrictRedis(connection_pool=pool)

# Neo4j
graph = Graph(f"bolt://{gateway}:7687", Name="neo4j", password="12345678")


# elasticsearch
es_connection = Elasticsearch([{"host": gateway, "port": 8013}])
