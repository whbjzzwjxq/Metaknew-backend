import redis
second = 1
minute = 60
hour = 3600
day = 24 * 3600
week = 7 * 24 * 3600
month = 30 * 24 * 3600

pool = redis.ConnectionPool(host='39.96.10.154', port=6379, db=1)
redis = redis.StrictRedis(connection_pool=pool)


def set_message(phone, message):
    return redis.setex(name=phone, time=minute, value=message)


def check_message(phone):
    current = redis.get(phone)
    return current.decode()


def query_location_queue():
    return redis.smembers('location_queue').decode()


def remove_location_queue(locations):
    return redis.srem('location_queue', locations)


def set_location_queue(locations):
    return redis.sadd('location_queue', locations)


def query_word_index(word_list):
    index = redis.hmget('word_index', word_list)
    return index.decode()


def query_index_word(indexes):
    word_list = redis.hmget('index_word', indexes)
    return word_list.decode()


def set_word_index(word_list, index_list):
    # todo redis事务 level: 2
    assert len(word_list) == len(index_list)
    if len(word_list) > 0:
        word_index = {word: index for word, index in zip(word_list, index_list)}
        index_word = {index: word for word, index in zip(word_list, index_list)}
        a = redis.hmset('word_index', word_index)
        b = redis.hmset('index_word', index_word)
        return a and b
    else:
        return True
