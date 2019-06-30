# ! /usr/bin/python
# encoding:utf-8

# Create your tasks here

from __future__ import absolute_import, unicode_literals

from celery import Celery

from document import models

app = Celery(__name__, broker='amqp://guest:guest@localhost:5672//')


@app.task
def add(x, y):
    return x + y

# 新增专题
@app.task
def add_document(filedata = {}):
    doc = models.Document.objects.create(**filedata)
    return doc

# 新增专题信息
@app.task
def add_document_info(filedata={}):

    doc = models.Document_Information.objects.create(**filedata)
    return doc