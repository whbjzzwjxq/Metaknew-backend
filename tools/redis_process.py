import redis
second = 1
minute = 60
hour = 3600
day = 24 * 3600
week = 7 * 24 * 3600
month = 30 * 24 * 3600

pool = redis.ConnectionPool(host='39.96.10.154', port=6379, db=1)
redis = redis.Redis(connection_pool=pool)
