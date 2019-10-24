from tools.redis_process import query_word_index, set_word_index, query_index_word
from tools.models import GlobalWordIndex
from django.shortcuts import HttpResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


# done in 07-24 完成了基础工作
# todo 词汇查询 level: 2
def query_word_list(word_list: list):
    """

    :param word_list:  词组 list
    :return: index list
    """
    index = query_word_index(word_list)
    uncached_words = [[loc, word] for loc, word in enumerate(word_list) if not index[loc]]
    un_index_words = []
    # todo index写入全局锁和备份 level:2
    if len(uncached_words) > 0:
        for loc_word in uncached_words:
            word = loc_word[1]
            loc = loc_word[0]
            try:
                record = GlobalWordIndex.objects.get(Word=word)
                index[loc] = record.WordIndex
            except ObjectDoesNotExist:
                un_index_words.append(loc_word)
        # 未记录的词语
        if len(un_index_words) > 0:
            new_record = [GlobalWordIndex(Word=loc_word[1]) for loc_word in un_index_words]
            records = GlobalWordIndex.objects.bulk_create(new_record)
            for i, record in enumerate(records):
                word = un_index_words[i][1]
                loc = un_index_words[i][0]
                if record.Word == word:
                    index[loc] = record.WordIndex
    set_word_index(word_list, index)
    return index


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
