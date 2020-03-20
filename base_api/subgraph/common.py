import json
from typing import List

from django.http import HttpResponse

from base_api.interface_frontend import ItemDraftBulkData
from base_api.logic_class import UserApi, HttpRequestUser
from record.logic_class import ItemHistory


class ItemApi(UserApi):
    abstract = True
    URL = 'item/'


class ItemDraftApi(ItemApi):
    abstract = True
    URL = 'draft/'


class DraftBulkUpdate(ItemDraftApi):
    """
    用一个草稿记录Content信息
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
        return {'DraftIdMap': ItemHistory.bulk_save(result)}

    def _response_hook(self, result) -> HttpResponse:
        return HttpResponse(status=200, content=json.dumps(result))


class VersionQuery(ItemApi):
    """
    查询单知识元所有草稿
    """
    abstract = False
    URL = ''


apis = [DraftBulkUpdate]
