import jwt


def make_token(user_name, user_id):
    # random 是生产环境启用的
    # secret = 'f0ba2016d24c545a' + ''.join(random.sample(string.ascii_letters + string.digits, 8))
    secret = 'f0ba2016d24c545a'
    content = {
        "name": user_name,
        "id": user_id
    }
    token = jwt.encode(content, secret, algorithm='HS256')
    token = str(token)
    return token
