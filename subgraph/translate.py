# -*- coding: utf-8 -*-
import sys
import uuid
import requests
import hashlib
import time
import json
import random

YOUDAO_URL = 'http://openapi.youdao.com/api'
APP_KEY = '2b44d851154f90ca'
APP_SECRET = 'lkY470moRMP7MdYFFoV5AOyMHbnb3v90'

BAIDU_URL = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
BAIDU_APPID = '20190414000287800'
BAIDU_SECRET = 'xry3tTDv1OUia6Jbxj2t'


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    if size <= 20:
        return q
    else:
        return q[0:10] + str(size) + q[size - 10:size]


def do_request_youdao(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_URL, data=data, headers=headers)


def connect(query, en2zh=True):
    q = query

    data = {}
    if en2zh:
        # data['from'] = 'EN'  源语言自动检测
        data['to'] = 'zh-CHS'
    else:
        data['to'] = 'EN'
        # data['from'] = 'zh-CHS'

    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign

    response = do_request_youdao(data)

    if "web" in json.loads(bytes.decode(response.content)).keys():
        # 优先使用网络释义
        result = json.loads(bytes.decode(response.content))
        return result["l"], result["web"][0]["value"][0]
    else:
        try:
            result = json.loads(bytes.decode(response.content))
            return result["l"], result["translation"][0]
        except:
            print(bytes.decode(response.content))
            return None, None


def translate(keyword, language_to, language_from='auto'):
    salt = random.randint(32768, 65536)
    m = hashlib.md5()
    sign = (BAIDU_APPID + keyword + str(salt) + BAIDU_SECRET).encode(encoding='utf-8')
    m.update(sign)
    sign = m.hexdigest()
    data = {'q': keyword,
            'to': language_to,
            'from': language_from,
            'appid': BAIDU_APPID,
            'salt': salt,
            'sign': sign}

    def do_request_baidu(data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(BAIDU_URL, data=data, headers=headers)

    response = bytes.decode(do_request_baidu(data).content)
    try:
        response = json.loads(response)
        if 'trans_result' in response:
            result = response['trans_result'][0]['dst']
            return result
    except:
        return None
