# -*- coding: utf-8 -*-
import requests
import hashlib
import json
import random

BAIDU_URL = "http://api.fanyi.baidu.com/api/trans/vip/translate"
BAIDU_APPID = "20190414000287800"
BAIDU_SECRET = "xry3tTDv1OUia6Jbxj2t"


def translate(keywords, language_to, language_from="auto"):
    salt = random.randint(32768, 65536)
    m = hashlib.md5()
    space = "\n"
    query = space.join(keywords)
    # query = urllib.parse.quote(query)
    sign = (BAIDU_APPID + query + str(salt) + BAIDU_SECRET).encode(encoding="utf-8")
    m.update(sign)
    sign = m.hexdigest()
    data = {"q": query,
            "to": language_to,
            "from": language_from,
            "appid": BAIDU_APPID,
            "salt": salt,
            "sign": sign}

    def do_request_baidu(data):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return requests.post(BAIDU_URL, data=data, headers=headers)

    response = bytes.decode(do_request_baidu(data).content)
    try:
        response = json.loads(response)
        if "trans_result" in response:
            result = response["trans_result"][0]["dst"]
            return result
    except AttributeError:
        return None

