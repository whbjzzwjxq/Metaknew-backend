# -*- coding: utf-8 -*-
import sys
import uuid
import requests
import hashlib
import time
import json

YOUDAO_URL = 'http://openapi.youdao.com/api'
APP_KEY = '2b44d851154f90ca'
APP_SECRET = 'lkY470moRMP7MdYFFoV5AOyMHbnb3v90'


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


def do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_URL, data=data, headers=headers)


def connect(query,en2zh=True):
    q = query

    data = {}
    if en2zh:
        data['from'] = 'EN'
        data['to'] = 'zh-CHS'
    else:
        data['to'] = 'EN'
        data['from'] = 'zh-CHS'
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

    response = do_request(data)

    if "web" in json.loads(bytes.decode(response.content)).keys():
        #优先使用网络释义
        return json.loads(bytes.decode(response.content))["web"][0]["value"][0]
    else:
        try:
            return json.loads(bytes.decode(response.content))["translation"][0]
        except:
            # print(q)
            print(bytes.decode(response.content))


if __name__ == '__main__':
    connect()