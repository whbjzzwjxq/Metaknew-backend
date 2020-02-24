import datetime
import json
from datetime import date
from functools import reduce

import langdetect
from py2neo import NodeMatcher, RelationshipMatcher

from tools.global_const import graph


class NeoSet:
    def __init__(self):
        self.tx = graph.begin()
        self.Nmatcher = NodeMatcher(graph)
        self.Rmatcher = RelationshipMatcher(graph)

    def match_node(self, query_object):
        """

        :param query_object: {_id, _type, _label}
        :return:
        """
        return self.Nmatcher.match([query_object['_type'], query_object['_label']], _id=query_object['_id'])

    def match_link(self, query_object):
        return self.Rmatcher.match(r_type=query_object['_label'], _id=query_object['_id'])


def language_detect(text):
    lang = langdetect.detect(text)
    if lang == 'zh_cn' or lang == 'zh_tw':
        lang = 'zh'
    elif lang == 'en':
        lang = 'en'
    else:
        lang = 'auto'
    return lang


def merge_list(lists):
    """
    合并并去重list
    :param lists:
    :return:
    """

    def merge(list1: list, list2: list):
        temp = [ele for ele in list2 if ele not in list1]
        list1.extend(temp)
        return list1

    result = reduce(merge, lists)
    return result


def filter_to_two_part(target_list, _func):
    """
    把list分为两类
    :param target_list:目标的队列
        :param _func: 目标函数
    :return:
    """
    positive_list = []
    negative_list = []
    for item in target_list:
        if _func(item):
            positive_list.append(item)
        else:
            negative_list.append(item)
    return positive_list, negative_list


class DateTimeEncoder(json.JSONEncoder):
    """
    DateTime 转为字符串
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, obj)
