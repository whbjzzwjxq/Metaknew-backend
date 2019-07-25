import re
from subgraph.models import *
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from document.models import DocGraph
from functools import reduce
from history.logic_class import AddRecord
from tools.redis_process import query_word_index, set_word_index, query_index_word
from tools.models import GlobalWordIndex
from django.shortcuts import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from tools.id_generator import id_generator, device_id

re_for_uuid = re.compile(r'\w{8}(-\w{4}){3}-\w{12}')
re_for_ptr = re.compile(r'.*_ptr')
graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
types = ['StrNode', 'InfNode', 'Media', 'Document']


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)


class_table = {
    'Base': NodeInfo,
    'Person': Person,
    'Project': Project,
    'ArchProject': ArchProject,
    'Document': DocGraph,
}


def init(label):
    if label in class_table:
        return class_table[label]
    else:
        return NodeInfo


def get_user_props(p_label: str):
    """
    :param p_label: PrimaryLabel
    :return: 不包含BaseNode字段信息的列表
    注意p_label = Document进行了特殊处理
    """
    remove_list = ['_id', 'PrimaryLabel', 'Name', 'MainPic', 'IncludedMedia', 'Description']
    if not p_label == 'Document':
        try:
            # 目标包含的域
            target = class_table[p_label]._meta.get_fields()
            result = [field.name for field in target
                      if not re_for_ptr.match(field.name)
                      and field.name not in remove_list]
            return result
        except AttributeError('没有这种标签: %s' % p_label):
            return []
    else:
        # todo document level: 0
        return ["Title", "MainPic", "Area", "CreateUser", "Description", "Keywords"]


def dict_dryer(node: dict):
    dry_prop = ['_id', 'type', 'PrimaryLabel']
    for key in dry_prop:
        if key in node:
            node.pop(key)
    return node


def merge_list(lists):
    def merge(list1: list, list2: list):
        temp = [ele for ele in list2 if ele not in list1]
        list1.extend(temp)
        return list1

    result = reduce(merge, lists)

    return result


class IdGenerationError(BaseException):
    # todo id 生成异常 level: 2
    pass


def error_check(_func):
    def wrapped(self, node):
        try:
            result = _func(self, node)
            return result
        except Exception as e:
            name = type(e).__name__
            AddRecord.add_error_record(user=self.user,
                                       source_id=self._id,
                                       source_label=self.label,
                                       data=node,
                                       bug_type=name)
            return False
            # todo 消息队列 level: 1

    return wrapped


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
            id_list = id_generator(number=len(un_index_words), method='word', content=device_id, jump=1)
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
                result.append('unknown')
    set_word_index(uncached_word, uncached_index)
    return result


def word_request(request):
    word = request.GET.get('word')
    index = query_word_list(word)
    return HttpResponse(index)
