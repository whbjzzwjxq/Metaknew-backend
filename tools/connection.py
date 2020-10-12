import os
import redis
from elasticsearch import Elasticsearch
from py2neo import Graph

postgre_container_name = os.getenv("POSTGRE_NAME", "postgre_container")
redis_container_name = os.getenv("REDIS_NAME", "redis_container")
neo4j_container_name = os.getenv("NEO4J_NAME", "neo4j_container")
es_container_name = os.getenv("ES_NAME", "es_container")

# postgresql
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "metaknew_production",
        "USER": "metaknew",
        "PASSWORD": "12345678",
        "HOST": postgre_container_name,
        "PORT": "5432",
    }
}

# redis
pool = redis.ConnectionPool(host=redis_container_name, port=6379, db=1, decode_responses=True)
redis_instance = redis.StrictRedis(connection_pool=pool)

# Neo4j
graph = Graph(f"bolt://{neo4j_container_name}:7687", Name="neo4j", password="12345678")

# elasticsearch
es_connection = Elasticsearch([{"host": es_container_name, "port": 9200}])
