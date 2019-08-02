import difflib
import regex
import random
import time
import random
from tools.redis_process import redis
from functools import reduce
import gzip


class JsonChangedCompress:
    operate = {
        # dict相关操作
        "add": 0,  # 添加键值
        "pop": 1,  # 去除键值
        "set_attr": 2,  # 设置值
        "clear": 3,  # 清空字典

        # list相关操作
        "append": 4,  # 末尾添加元素
        "delete": 5,  # 删除元素
        "copy": 6,  # 复制元素

        # string相关操作
        "plus": 7,  # 某位置插入字符串
        "remove": 8,  # 某位置去除字符串
    }

    def __init__(self, json_regex, str_regex, def_replace="|", short_str=8, long_str=512,
                 float2int=True, ordered=True, choose=False, use_json_schema=True, use_re_base=True):
        """

        :param json_regex: json匹配模板， 默认是预编译的正则表达式
        :param str_regex: string匹配模板
        :param def_replace: 默认分隔符
        :param short_str: 视为小文本的字符数量
        :param long_str: 视为大文本的字符数量
        :param float2int: 是否将浮点数取整
        :param ordered: 是否保持数组有序
        :param use_json_schema: json匹配方式， 正则匹配或者jsonschema匹配
        :param use_re_base: 是否使用默认的字符串匹配
        """
        self.json_schema = json_regex
        self.json_index = {schema: i for i, schema in enumerate(json_regex)}

        self.def_replace = def_replace
        self.re_end = regex.compile("\\" + self.def_replace + "\w{0,5}")
        self.str_schema = [{"schema": regex.compile(r"(\w{8}-)(\w{4}-)(\w{4}-)(\w{4}-)(\w{12})"),
                            "replace": self.def_replace,
                            "base": []},
                           {"schema": regex.compile("(\d{4}-)(\d{2}-)(\d{2})(\s\d{2}:\d{2}:\d{2})(.\d{6})"),
                            "replace": self.def_replace,
                            "base": []},
                           {"schema": regex.compile("(\d{4}-)(\d{2}-)(\d{2})"),
                            "replace": self.def_replace,
                            "base": []}]
        if use_re_base:
            self.str_schema.append(str_regex)
        else:
            self.str_schema = str_regex

        self.str_index = {schema: i for i, schema in enumerate(str_regex)}

        self.float2int = float2int
        self.long_str = long_str
        self.short_str = short_str

        self.ordered = ordered
        self.ran_temp = choose
        self.use_json_schema = use_json_schema

    def compress(self, instance):
        if isinstance(instance, dict):
            return self.__com_dict(instance)
        elif isinstance(instance, list):
            return self.__com_list(instance)
        else:
            print("不需要压缩的类型")
            return None

    def decompress(self):
        pass

    def __com_dict(self, _dict):
        pass

    def __com_list(self, _list):
        pass

    def __com_string(self, _string):
        pass

    def __com_other(self, _other):
        pass

    def pack_dict(self, _dict1, _dict2):
        pass

    def pack_list(self, _list1, _list2):
        pass

    def pack_string(self, _str, _str2):
        """
        # 基于两种方法压缩，
        # 1 比对_str和pattern的匹配
        # 2 比对_str和_str2的差异,其中index是_str2的index
        :param _str: 想要压缩的字符串
        :param _str2: 作为基准的字符串
        :return:
        """

    def unpack_dict(self, _dict1, _dict2):
        pass

    def unpack_list(self, _list1, _list2):
        pass

    def unpack_string(self, _str1, _str2):
        pass

    def compare(self, _str, _str2):
        if len(_str) < self.short_str:
            temp = _str.replace(self.def_replace, "(%s)" % self.def_replace)
            return temp
        else:
            _back_str = ""
            temps = list(difflib.Differ().compare(_str, _str2))
            tag = " "
            for i, temp in enumerate(temps):
                if temp[0] == " ":
                    if not tag == " ":
                        tag = " "
                else:
                    if tag == temp[0]:
                        if temp[2] == "+" or temp[2] == "-":
                            _back_str += "(%s)" % temp[2]
                        else:
                            _back_str += temp[2]
                    else:
                        tag = temp[0]
                        _back_str += temp[0]
                        if temp[2] == "+" or temp[2] == "-":
                            _back_str += "(%s)" % temp[2]
                        else:
                            _back_str += temp[2]
            if len(_back_str) <= len(_str):
                return _back_str
            else:
                temp1 = _str[0:len(_str) - 6]
                temp2 = _str[len(_str) - 6:len(_str)]
                if regex.match(self.re_end, temp2):
                    temp2.replace(self.def_replace, "(%s)" % self.def_replace)
                return temp1 + temp2

    def pattern_match(self, _str):
        if self.short_str <= len(_str) <= self.long_str:
            _back_str = ""
            for i, pattern in enumerate(self.str_schema):
                re = pattern["schema"]
                result = regex.match(re, _str)

                if result:
                    result = list(result.groups())
                    if not pattern["base"]:
                        self.str_schema[i]["base"] = result
                        return "|"
                    base = pattern["base"]
                    replace = pattern["replace"]
                    if not len(base) == len(result):
                        print("似乎字符串: %s的分割长度: %d与基准长度: %d不一样" % (_str, len(result), len(base)))
                    min_len = min(len(base), len(result))
                    for index in range(0, min_len):
                        if base[index] == result[index]:
                            if index == 0 or index == len(result):
                                result[index] = replace
                            elif result[index - 1] == replace:
                                result[index] = replace
                            else:
                                result[index] = replace * 2
                        else:
                            result[index].replace(replace, "(%s)" % replace)
                        _back_str += result[index]
                    if len(result) > len(base):
                        more = "".join(result[len(base):len(result)])
                        _back_str += more
                        # method = match
                    _back_str += "%s%d" % (self.def_replace, i)
                    if not _back_str == "":
                        return _back_str
                    else:
                        return None
                else:
                    pass


#
# a = "bddc3df2-001b-0000-8fb1-408d5cb77abb"
# b = "bdd23df2-001b-0010-8fb1-408d5cb77ab1"
#
# c = JsonChangedCompress([], [], def_replace="|")
# print(c.compare(a, b))
