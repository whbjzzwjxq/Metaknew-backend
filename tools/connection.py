import os
import redis
from elasticsearch import Elasticsearch
from py2neo import Graph

localhost = os.getenv("LOCALHOST")

postgres_port = os.getenv("POSTGRES_PORT")
postgres_password = os.getenv("POSTGRES_PASSWORD")
postgres_user = os.getenv("POSTGRES_USER")
postgres_db = os.getenv("POSTGRES_DB")

redis_port = os.getenv("REDIS_PORT")

neo4j_port = os.getenv("NEO4J_PORT_BOLT")
neo4j_password = os.getenv("NEO4J_PASSWORD")

es_port_api = os.getenv("ES_PORT_API")

# postgresql
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": postgres_db,
        "USER": postgres_user,
        "PASSWORD": postgres_password,
        "HOST": localhost,
        "PORT": postgres_port,
    }
}

# redis
pool = redis.ConnectionPool(host=localhost, port=redis_port, db=1, decode_responses=True)
redis_instance = redis.StrictRedis(connection_pool=pool)

# neo4j
graph = Graph(f"bolt://{localhost}:{neo4j_port}", Name="neo4j", password=neo4j_password)

# elasticsearch
es_connection = Elasticsearch([{"host": localhost, "port": es_port_api}])
