import redis

pool = redis.ConnectionPool(host='39.96.10.154', port=6379, db=1)
red = redis.Redis(connection_pool=pool)
