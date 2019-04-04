# -*-coding=utf-8 -*-
from django.shortcuts import render
from document import comment,document_info
import datetime as dt
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from playhouse.shortcuts import model_to_dict, dict_to_model

# Create your views here.
@csrf_exempt
# 根据专题id得到评论
def get_comments(request):
    comment_id = request.POST['id']
    comments = comment.selectById(comment_id)
    #return render(request, 'comment.html', {'comments': comments})
    #model_to_dict(comments)
    return HttpResponse(json.dump(comments), content_type="application/json")

# 添加评论
def add_comment(request):
    if request.POST['content'] == 'null':
        return render(request,'comment.html',{})
    filedata = {}
    filedata['uuid'] = request.POST['uuid']
    filedata['userid'] = request.POST['userid']
    filedata['time'] = dt.datetime.now()
    filedata['content'] = request.POST.get('content')
    filedata['star'] = request.POST['star']
    comm = comment.add(filedata)

    #return render(request,'comment.html',{'comment:':comm})
    return HttpResponse(json.dumps(comm), content_type="application/json")

# 根据commentID 更新评论
def update_comment(request):
    if request.POST['id'] == 'null':
        return render(request,'comment.html',{})

    if request.POST['content'] == 'null':
        return render(request,'comment.html',{})

    id = request.POST['id']
    filedata = {}
    filedata['uuid'] = request.POST['uuid']
    filedata['userid'] = request.POST['userid']
    filedata['time'] = dt.datetime.now()
    filedata['content'] = request.POST['content']
    filedata['star'] = request.POST['star']
    res = comment.updateById(id,filedata)

    return render(request,'comment.html',{'res':res})

# 根据commentId删除评论
def delete_comment(request):
    if request.POST['id'] == 'null':
        return render(request,'comment.html',{})
    id = request.POST['id']
    res = comment.deleteById(id)

    return render(request,'comment.html',{'res':res})

#根据专题id得到专题info
def get_doc_info(request):
    doc_id = request.POST['id']
    docs = document_info.selectById(doc_id)
    # return render(request, 'comment.html', {'comments': comments})
    # model_to_dict(comments)
    return HttpResponse(str(docs), content_type="application/json")