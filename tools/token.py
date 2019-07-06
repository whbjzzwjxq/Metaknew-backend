import jwt
from django.core.cache import cache

second = 1
minute = 60
hour = 3600
day = 24*3600
week = 7*24*3600
month = 30*24*3600


def make_token(user_name, user_id):
    secret = 'f0ba2016d24c545a'
    content = {
        "name": user_name,
        "id": user_id
    }
    token = jwt.encode(content, secret, algorithm='HS256')
    cache.add(user_name, user_id, timeout=week)
    cache.add(user_id, token, timeout=week)
    return token

