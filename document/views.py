# -*-coding=utf-8 -*-
import json
import re
from datetime import datetime

from django.http import HttpResponse

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

    # id判断
    re_for_old_id = re.compile('\\$_.*')
    if re_for_old_id.match(str(graph["id"])):
        doc_id = id_generator(number=1, method="node", jump=3)[0]
    else:
        doc_id = graph["id"]

    if is_auto:
        draft_list = UserDraft.objects.filter(UserId=user_id, SourceId=doc_id)
        if not draft_list:
            latest_draft_id = 1
        else:
            latest_draft_id = draft_list.latest('UpdateTime').VersionId % 5 + 1
        graph["id"] = doc_id
        new_draft = UserDraft(
            UserId=user_id,
            SourceId=doc_id,
            SourceType='document',
            VersionId=latest_draft_id,
            Name='autoSave' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            Content=graph
        )
        new_draft.save()
        return HttpResponse(json.dumps({'node': {doc_id: graph['id']}}), status=200)
    else:
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

