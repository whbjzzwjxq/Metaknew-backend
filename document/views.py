# -*-coding=utf-8 -*-
import json
import re
from datetime import datetime
from typing import List

from django.db.models import Max
from django.http import HttpResponse
from django.core import serializers
from document.class_document import DocGraphClass
from tools.base_tools import DateTimeEncoder, NeoSet, bulk_save_base_model
from tools.id_generator import id_generator
from users.logic_class import BaseUser
from users.models import UserDraft


def query_graph(request):
    _id = request.GET.get('_id')
    user_id = request.GET.get("user_id")
    if user_id == 'None' or not user_id:
        user_id = 1
    graph = DocGraphClass(_id=_id, user_id=user_id)
    graph.query_base()
    result = {"id": _id, "node": graph.handle_for_frontend_as_graph()}

    return HttpResponse(json.dumps(result, cls=DateTimeEncoder))


def create_graph(request):
    collector = NeoSet()
    data = json.loads(request.body.decode())
    user_id = request.GET.get("user_id")
    graph = data["graph"]
    is_draft = data["isDraft"]
    is_auto = data["isAuto"]

    if is_auto:
        # 绑定一下id
        doc_id = graph["draftId"]
        if doc_id == -1:
            doc_id = id_generator(number=1, method="device", jump=3)[0]
        new_draft = UserDraft(
            UserId=user_id,
            SourceId=doc_id,
            SourceType='document',
            Content=graph
        )
        draft_list = UserDraft.objects.filter(UserId=user_id, SourceId=doc_id)
        if not draft_list:
            new_draft.VersionId = 1
        else:
            latest_draft = draft_list.aggregate(Max('VersionId'))
            if latest_draft["VersionId__max"] < 5:
                new_draft.VersionId = latest_draft["VersionId__max"] + 1
            else:
                new_draft = draft_list.earliest('UpdateTime')
        name = graph["name"] + 'autoSave' + str(new_draft.VersionId)
        new_draft.Name = name
        new_draft.save()
        return HttpResponse(doc_id, status=200)
    else:
        # id判断
        re_for_old_id = re.compile('\\$_.*')
        if re_for_old_id.match(str(graph["id"])):
            doc_id = id_generator(number=1, method="node", jump=3)[0]
        else:
            doc_id = graph["id"]
        user_model = BaseUser(_id=user_id).query_user()
        doc = DocGraphClass(_id=doc_id, user_id=user_id, collector=collector)
        if re_for_old_id.match(str(graph["id"])):
            document = doc.graph_create(graph)
        else:
            document = doc.graph_update(graph, is_draft)

        if is_draft:
            document.new_history.save()
        else:
            document.graph.save()
            if document.new_history:
                document.new_history.save()
            doc_to_node_links = document.doc_to_node_links
            bulk_save_base_model(doc_to_node_links, user_model, "link")

        nodes = [node for node in document.info_change_nodes if node.type != 'media']
        medias = [media for media in document.info_change_nodes if media.type == 'media']
        links = document.info_change_links
        bulk_save_base_model(nodes, user_model, "node")
        bulk_save_base_model(medias, user_model, "media")
        bulk_save_base_model(links, user_model, "link")
        collector.tx.commit()
        result = {'node': document.node_id_old_new_map, 'link': document.link_id_old_new_map}
        return HttpResponse(json.dumps(result), status=200)


def query_auto_save(request):

    def handle_for_frontend(auto_save_list: List[UserDraft]):
        result = []
        for auto_save in auto_save_list:
            result.append({
                'UpdateTime': str(auto_save.UpdateTime.strftime("%Y-%m-%d %H:%M:%S")),
                'Content': auto_save.Content,
                'DontClear': auto_save.DontClear,
                'Name': auto_save.Name,
                'VersionId': auto_save.VersionId,
                'SourceId': auto_save.SourceId
            })
        return result

    user_id = request.GET.get('user_id')
    start = request.GET.get('start')
    start = int(start)
    user_id = int(user_id)
    user_auto_save = UserDraft.objects.filter(UserId=user_id).filter(Deleted=False)
    if user_auto_save:
        return_auto_save = user_auto_save.order_by('UpdateTime')[start: start + 10]
        if len(return_auto_save) == 0:
            return HttpResponse('empty', status=202)
        else:
            return HttpResponse(json.dumps(handle_for_frontend(return_auto_save)), status=200)
    else:
        return HttpResponse('empty', status=202)


def delete_auto_save(request):
    user_id = request.GET.get('user_id')
    source = int(request.GET.get('source'))
    version = int(request.GET.get('version'))
    draft_list = UserDraft.objects.filter(UserId=user_id, SourceId=source, VersionId=version)
    if draft_list:
        for draft in draft_list:
            draft.Deleted = True
            draft.save()
    return HttpResponse(status=200)
