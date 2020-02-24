import redis
from users.models import User, Privilege
from django.core.exceptions import ObjectDoesNotExist
second = 1
minute = 60
hour = 3600
day = 24 * 3600
week = 7 * 24 * 3600
month = 30 * 24 * 3600

pool = redis.ConnectionPool(host="39.96.10.154", port=6379, db=1, decode_responses=True)
redis_instance = redis.StrictRedis(connection_pool=pool)


# 集中redis的原因是防止误设置键值
# 纯数字键 是user登录使用


# ----------------user登录相关
def user_set_message(phone, message):
    print(message)
    return redis_instance.setex(name="phone_" + phone, time=4 * minute, value=message)


def user_check_message(phone):
    current = redis_instance.ttl("phone_" + phone)
    # 大于120秒则没有失效
    if current >= 120:
        return True
    else:
        return False


def user_query_message(phone):
    return redis_instance.get("phone_" + phone)


def user_login_set(user: User, privilege: Privilege, token):
    name = user.Name
    _id = user.UserId
    with redis_instance.pipeline(transaction=True) as pipe:
        pipe.multi()
        pipe.set(_id, token, ex=week)
        pipe.set("user_" + name, _id, ex=week)
        # 该用户拥有的各种权限
        for field in privilege._meta.get_fields():
            if field.name != "UserId":
                name = field.name + "_" + str(_id)
                value = getattr(privilege, field.name)
                if value:
                    pipe.sadd(name, *value)
        pipe.execute()


def group_privilege_set(_id, privilege):
    with redis_instance.pipeline(transaction=True) as pipe:
        pipe.multi()
        for field in Privilege._meta.get_fields():
            if field.name != "UserId":
                name = field.name + "_group_" + str(_id)
                value = getattr(privilege, field.name)
                if value:
                    pipe.sadd(name, *value)
        pipe.execute()


def user_group_privilege_info_query(_id):
    result = {}
    with redis_instance.pipeline() as pipe:
        pipe.multi()
        for field in Privilege._meta.get_fields():
            if field.name != "UserId":
                name = field.name + "_group_" + str(_id)
                value = pipe.smembers(name)
                if value:
                    result.update({field.name: value})
    return result


def user_query_by_name(name):
    # todo 事务操作 level: 2
    _id = redis_instance.get("user_" + name)
    if _id:
        token = redis_instance.get(_id)
        return _id, token
    else:
        return None, None


def user_query_info_by_id(_id):
    # 是游客就返回None
    if str(_id) == "0":
        return None
    else:
        # info 定义 上方cache_info
        info = redis_instance.hgetall("user_info_" + str(_id))
        info = {key: bool(value) for key, value in info.items()}

        # join_group定义 上方
        join_group = redis_instance.hgetall("join_group_" + str(_id))
        privilege = {}
        for field in Privilege._meta.get_fields():
            if field.name != "UserId":
                name = field.name + "_" + str(_id)
                value = redis_instance.smembers(name)
                privilege.update({field.name: value})
        return {"bool_info": info, "joint_group": join_group, "privilege": privilege}


def get_user_name(user_id):
    try:
        user = User.objects.get(pk=user_id)
        return user.Name
    except ObjectDoesNotExist:
        return None


# ----------------名字翻译 地名转译相关
def query_location_queue():
    return redis_instance.smembers("location_queue")


def remove_location_queue(locations):
    return redis_instance.srem("location_queue", locations)


def set_location_queue(locations):
    return redis_instance.sadd("location_queue", *locations)


def set_translate_queue(name, _id):
    return redis_instance.set("translation_" + _id, name)


# ----------------word_index相关

def query_word_index(word_list):
    index = redis_instance.hmget("word_index", word_list)
    return index


def query_index_word(indexes):
    word_list = redis_instance.hmget("index_word", indexes)
    return word_list


def set_word_index(word_list, index_list):
    # todo redis事务 level: 2
    assert len(word_list) == len(index_list)
    if len(word_list) > 0:
        word_index = {word: index for word, index in zip(word_list, index_list)}
        index_word = {index: word for word, index in zip(word_list, index_list)}
        a = redis_instance.hmset("word_index", word_index)
        b = redis_instance.hmset("index_word", index_word)
        return a and b
    else:
        return True


# ----------------标签-属性
def query_needed_prop(plabel):
    prop_dict = redis_instance.hgetall("plabel_" + plabel)
    if prop_dict:
        return prop_dict
    else:
        return {}


def set_needed_prop(plabel, prop_dict):
    key = "plabel_" + plabel
    current = redis_instance.hkeys(key)
    if len(current) > 0:
        redis_instance.hdel(key, *current)
    redis_instance.hmset(key, prop_dict)
    return True


def query_available_plabel():
    plabel_list = redis_instance.smembers("plabel_list")
    if plabel_list:
        return plabel_list
    else:
        return []


def mime_type_query():
    return redis_instance.hgetall("mime_type")


def mime_type_set(mime_type_dict):
    redis_instance.hmset("mime_type", mime_type_dict)


def set_un_index_text(id_list: list):
    return redis_instance.sadd("un_index_text", *id_list)


def set_un_index_node(id_list: list):
    return redis_instance.sadd("un_index_node", *id_list)
