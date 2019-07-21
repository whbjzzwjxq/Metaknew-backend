import jwt
import random
import string


def make_token(user_name, user_id):
    secret = 'f0ba2016d24c545a' + ''.join(random.sample(string.ascii_letters + string.digits, 8))
    # secret = 'f0ba2016d24c545a'
    content = {
        "name": user_name,
        "id": user_id
    }
    token = jwt.encode(content, secret, algorithm='HS256')
    token = str(token)
    return token
