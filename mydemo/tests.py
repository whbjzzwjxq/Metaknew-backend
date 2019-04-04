import psycopg2
from django.test import TestCase

import mydemo.views as test
# Create your tests here.


if __name__ == '__main__':
    obj = test.TestMongoEngine()
    # obj.creat()
    # obj.add("张三", "总经理", "13070167585", "百度", "有关经理的相关介绍", "123456@163.com", "五道口")
    # obj.delete("1")
    obj.selectByID("2")