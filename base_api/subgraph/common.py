import json
from typing import List, Tuple

from django.http import HttpResponse

from base_api.interface_frontend import ItemDraftBulkData
from base_api.logic_class import UserApi, HttpRequestUser
from record.exception import ErrorForWeb, IdGenerationError
from record.logic_class import ItemHistory
from tools.global_const import re_for_frontend_id
from tools.id_generator import id_generator


class ItemApi(UserApi):
    abstract = True
    URL = 'item/'


class ItemDraftApi(ItemApi):
    abstract = True
    URL = 'draft/'


class DraftBulkCreate(ItemDraftApi):
    abstract = False
    URL = 'bulk_create'
    frontend_data = ItemDraftBulkData
    method = 'POST'
    meta = ItemDraftApi.meta.rewrite()

    def _main_hook(self, result: ItemDraftBulkData, request: HttpRequestUser) -> Tuple[List[ItemHistory], dict]:
        data_list = result.Data
        user_model = request.user
        old_new_id_map = {}
        model_list = []
        if result.IsNode:
            method = 'node'
        else:
            method = 'link'
        id_list = id_generator(len(data_list), method=method)
        for data, remote_id in zip(data_list, id_list):
            # 检查是否是客户端id 如果不是报错 调用错了方法
            old_id = str(data.Query.id)
            if re_for_frontend_id.match(old_id):
                old_new_id_map[old_id] = remote_id
                data.Query.id = remote_id
            else:
                ErrorForWeb(IdGenerationError, description='客户端id的item才调用生成方法', is_dev=True,
                            is_error=True).raise_error()
            record_model = ItemHistory(user_id=user_model.user_id, query_object=data.Query)
            record_model.record_update(content=data, is_auto=result.IsAuto, is_draft=True, create_type=result.CreateType)
            model_list.append(record_model)
        return model_list, old_new_id_map

    def _save_hook(self, result: Tuple[List[ItemHistory], dict]):
        return {'DraftIdMap': ItemHistory.bulk_save(result[0]), 'IdMap': result[1]}

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


class DraftBulkUpdate(ItemDraftApi):
    """
    注意是更新草稿 还是添加了记录
    """
    abstract = False
    URL = 'bulk_update'
    frontend_data = ItemDraftBulkData
    method = 'POST'
    meta = ItemDraftApi.meta.rewrite()

    def _main_hook(self, result: ItemDraftBulkData, request: HttpRequestUser) -> List[ItemHistory]:
        data_list = result.Data
        user_model = request.user
        model_list = [
            ItemHistory(user_id=user_model.user_id, query_object=data.Query, version=data.VersionId).record_update(
                content=data, create_type=result.CreateType, is_auto=result.IsAuto, is_draft=True)
            for data in data_list
        ]
        return model_list

    def _save_hook(self, result: List[ItemHistory]):
        return {'DraftIdMap': ItemHistory.bulk_save(result), 'IdMap': {}}

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


class VersionQuery(ItemApi):
    """
    查询单知识元所有草稿
    """
    abstract = False
    URL = ''


apis = [DraftBulkCreate, DraftBulkUpdate]
