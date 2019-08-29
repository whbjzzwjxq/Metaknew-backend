import redis
import typing
from users.models import User, Privilege

second = 1
minute = 60
hour = 3600
day = 24 * 3600
week = 7 * 24 * 3600
month = 30 * 24 * 3600

pool = redis.ConnectionPool(host="39.96.10.154", port=6379, db=1)
redis = redis.StrictRedis(connection_pool=pool)


# 集中redis的原因是防止误设置键值
# 纯数字键 是user登录使用


# ----------------user登录相关
def user_set_message(phone, message):
    return redis.setex(name="phone_" + phone, time=5 * minute, value=message)


def user_check_message(phone):
    current = redis.ttl("phone_" + phone)
    if current >= 120:
        return True
    else:
        return False


def user_query_message(phone):
    return redis.get("phone_" + phone).decode()


def user_login_set(user: User, privilege: Privilege, token):
    name = user.UserName
    _id = user.UserId
    with redis.pipeline(transaction=True) as pipe:
        pipe.multi()
        pipe.set(_id, token, ex=week)
        pipe.set("user_" + name, _id, ex=week)
        cache_info = {
            "Is_Superuser": user.Is_Superuser,
            "Is_Developer": user.Is_Developer,
            "Is_Publisher": user.Is_Publisher,
            "Is_Vip": user.Is_Vip,
            "Is_high_vip": user.Is_high_vip,
            "Is_Active": user.Is_Active,
            "Is_Banned": user.Is_Banned
        }
        cache_info.update(user.Joint_Group)
        cache_info = {key: bytes(value) for key, value in cache_info.items()}
        pipe.hmset("info_" + str(_id), cache_info)
        for field in privilege._meta.get_fields():
            if field.name != "UserId":
                name = field.name + "_" + str(_id)
                value = getattr(privilege, field.name)
                if value:
                    pipe.sadd(name, *value)
        pipe.execute()


def user_query_by_name(username):
    # todo 事务操作 level: 2
    _id = redis.get("user_" + username)
    token = redis.get(_id)
    return _id, token


def user_query_info_by_id(_id):
    info = redis.hgetall("info_" + str(_id))
    info = {key.decode(): value.decode() for key, value in info.items()}
    return info


# ----------------名字翻译 地名转译相关
def query_location_queue():
    return redis.smembers("location_queue").decode()


def remove_location_queue(locations):
    return redis.srem("location_queue", locations)


def set_location_queue(locations):
    return redis.sadd("location_queue", locations)


def query_untranslated_name():
    pass


# ----------------word_index相关
def query_word_index(word_list):
    index = redis.hmget("word_index", word_list)
    return index.decode()


def query_index_word(indexes):
    word_list = redis.hmget("index_word", indexes)
    return word_list.decode()


def set_word_index(word_list, index_list):
    # todo redis事务 level: 2
    assert len(word_list) == len(index_list)
    if len(word_list) > 0:
        word_index = {word: index for word, index in zip(word_list, index_list)}
        index_word = {index: word for word, index in zip(word_list, index_list)}
        a = redis.hmset("word_index", word_index)
        b = redis.hmset("index_word", index_word)
        return a and b
    else:
        return True


# ----------------标签-属性
def query_needed_prop(plabel):
    prop_dict = redis.hgetall("plabel_" + plabel)
    if prop_dict:
        prop_dict: typing.Dict[bytes: bytes] = {key.decode(): value.decode() for key, value in prop_dict.items()}
        return prop_dict
    else:
        return {}


def set_needed_prop(plabel, prop_dict):
    key = "plabel_" + plabel
    current = redis.hkeys(key)
    if len(current) > 0:
        redis.hdel(key, *current)
    redis.hmset(key, prop_dict)
    return True


def query_available_plabel():
    plabel_list = redis.smembers("plabel_list")
    if plabel_list:
        plabel_list: typing.Set[bytes] = [plabel.decode() for plabel in plabel_list]
        return plabel_list
    else:
        return []
