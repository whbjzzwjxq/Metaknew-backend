import redis
import typing
import json
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
def set_message(phone, message):
    return redis.setex(name="phone_" + phone, time=5 * minute, value=message)


def check_message(phone):
    current = redis.ttl("phone_" + phone)
    if current >= 120:
        return True
    else:
        return False


def set_user_login(user, token):
    name = user.UserName
    _id = user.UserId
    redis.set(_id, token, ex=week)
    redis.set("user_" + name, _id, ex=week)
    cache_info = {
        "root": user.Is_Superuser,
        "dev": user.Is_Developer,
        "publish": user.Is_Publisher,
        "vip": user.Is_Vip,
        "high_vip": user.Is_high_vip
    }
    cache_info.update(user.Joint_Group)
    cache_info = {key: bytes(value) for key, value in cache_info.items()}
    redis.hmset("info_" + str(_id), cache_info)


def query_user_by_name(username):
    # todo 事务操作 level: 2
    _id = redis.get("user_" + username)
    token = redis.get(_id)
    return _id, token


def query_message(phone):
    return redis.get("phone_" + phone).decode()


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
        prop_dict: typing.Dict[bytes: bytes] = {key.decode(): value for key, value in prop_dict.items()}
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
