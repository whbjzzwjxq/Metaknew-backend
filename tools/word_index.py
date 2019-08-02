from tools.redis_process import query_word_index, set_word_index, query_index_word
from tools.models import GlobalWordIndex
from django.shortcuts import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from tools.id_generator import id_generator, device_id


# done in 07-24 完成了基础工作 todo 词汇查询 level: 2
def query_word_list(word_list):
    index = query_word_index(word_list)
    uncached_words = [[loc, word] for loc, word in enumerate(word_list) if not index[loc]]
    un_index_words = []
    # todo index写入全局锁和备份 level:2
    if len(uncached_words) > 0:
        for loc, loc_word in enumerate(uncached_words):
            word = loc_word[1]
            record = GlobalWordIndex.objects.filter(Word=word)  # test 写法的好坏
            if len(record) == 0:
                un_index_words.append([loc, word])  # 注意这里换了一次loc
            else:
                # 记录索引
                loc_word[1] = record[0].WordIndex
        # 未记录的词语
        if len(un_index_words) > 0:
            id_list = id_generator(number=len(un_index_words), method="word", content=device_id, jump=1)
            new_record = []
            for loc, loc_word in enumerate(un_index_words):
                new_record.append(GlobalWordIndex(WordIndex=id_list[loc], Word=loc_word[1]))
                loc_word[1] = id_list[loc]
                uncached_words[loc_word[0]][1] = id_list[loc]
            GlobalWordIndex.objects.bulk_create(new_record)
        for i in uncached_words:
            index[i[0]] = i[1]
    set_word_index(word_list, index)
    return index
    # todo 连接池 level: 2
    # todo important save : 重要的save过程是阻塞线程的 非重要的save过程不阻塞线程 level: 1
    # todo 缓存策略 level: 3


def index_to_word(index):
    word_list = query_index_word(index)
    result = []
    uncached_index = []
    uncached_word = []
    for loc, word in enumerate(word_list):
        if word:
            result.append(word)
        else:
            try:
                word = GlobalWordIndex.objects.get(WordIndex=index[loc])
                uncached_index.append(index[loc])
                uncached_word.append(word)
                result.append(word)
            except ObjectDoesNotExist:
                result.append("unknown")
    set_word_index(uncached_word, uncached_index)
    return result


def word_request(request):
    word = request.GET.get("word")
    index = query_word_list(word)
    return HttpResponse(index)