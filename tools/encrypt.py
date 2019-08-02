import jwt
import random
import string
from Crypto.Cipher import AES
from base64 import b64decode, b64encode
import regex
key_for_id = bytes("sZuaB4du1m3xiX6k", encoding="utf-8")
iv = b"5612347654327898"
block_size = 16
re_label_id = regex.compile("(\w*)(\|)(\d*)(h{0,15})")


def make_token(user_name, user_id):
    secret = "f0ba2016d24c545a" + "".join(random.sample(string.ascii_letters + string.digits, 8))
    # secret = "f0ba2016d24c545a"
    content = {
        "name": user_name,
        "_id": user_id
    }
    token = jwt.encode(content, secret, algorithm="HS256")
    token = str(token)
    return token


def padding(text, char):

    bytes_length = len(bytes(text, encoding="utf-8"))
    padding_length = block_size - bytes_length % block_size
    padding_text = bytes(char, encoding="utf-8") * padding_length

    return bytes(text, encoding="utf-8") + padding_text


def encode_id(label, auto_id):
    cipher = AES.new(key=key_for_id,
                     mode=AES.MODE_CBC,
                     iv=iv)
    content = padding(label + "|" + auto_id, "h")
    result = str(b64encode(cipher.encrypt(content)), encoding="utf-8")
    return result


def decode_id(content):
    cipher = AES.new(key=key_for_id,
                     mode=AES.MODE_CBC,
                     iv=iv)
    encrypt = b64decode(content)
    decrypt = cipher.decrypt(encrypt)
    result = str(decrypt, encoding="utf-8")
    result = regex.match(re_label_id, result).groups()
    return result[0], result[2]


def decode(content, length):
    cipher = AES.new(key=key_for_id,
                     mode=AES.MODE_CBC,
                     iv=iv)

    encrypt = b64decode(content)
    decrypt = cipher.decrypt(encrypt)
    result = str(decrypt, encoding="utf-8")[0:length]
    return result
