from tools.redis_process import redis
from tools.models import GlobalWordIndex
from django.shortcuts import HttpResponse


# 测试完成
def query_word(word):
    index = redis.hget('word_list', word)
    if index:
        return index
    else:
        record = GlobalWordIndex.objects.filter(Word=word)
        if len(record) == 0:
            index = GlobalWordIndex.objects.create(Word=word)
            index.save()
            redis.hset('word_list', word, index.id)
            return index.id
        else:
            index = word[0].id
            redis.hset('word_list', word, index)
            return index


def word_request(request):

    word = request.GET.get('word')
    index = query_word(word)
    return HttpResponse(index)
