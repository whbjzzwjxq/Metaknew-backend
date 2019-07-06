import jwt
from django.core.cache import cache
import random
import string

second = 1
minute = 60
hour = 3600
day = 24 * 3600
week = 7 * 24 * 3600
month = 30 * 24 * 3600


def make_token(user_name, user_id):
    # secret = 'f0ba2016d24c545a' + ''.join(random.sample(string.ascii_letters + string.digits, 8))
    secret = 'f0ba2016d24c545a'
    content = {
        "name": user_name,
        "id": user_id
    }
    token = jwt.encode(content, secret, algorithm='HS256')
    token = str(token)
    cache.add(user_name, user_id, timeout=week)
    cache.add(user_id, token, timeout=week)
    return token
