import os
import redis
from elasticsearch import Elasticsearch
from py2neo import Graph

support_host = os.getenv('SUPPORT_HOST', '127.0.0.1')
# postgre
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "metaknew_production",
        "USER": "metaknew",
        "PASSWORD": "12345678",
        "HOST": support_host,
        "PORT": "5432",
    }
}

# redis
pool = redis.ConnectionPool(host=support_host, port=6379, db=1, decode_responses=True)
redis_instance = redis.StrictRedis(connection_pool=pool)

# Neo4j
graph = Graph(f"bolt://{support_host}:7687", Name="neo4j", password="12345678")


# elasticsearch
es_connection = Elasticsearch([{"host": support_host, "port": 8013}])
