import redis
second = 1
minute = 60
hour = 3600
day = 24 * 3600
week = 7 * 24 * 3600
month = 30 * 24 * 3600

pool = redis.ConnectionPool(host='39.96.10.154', port=6379, db=1)
redis = redis.Redis(connection_pool=pool)


def user_login(user_name, user_id, token):
    redis.set(user_name, user_id, ex=week)
    redis.set(user_id, token, ex=week)

    pass

