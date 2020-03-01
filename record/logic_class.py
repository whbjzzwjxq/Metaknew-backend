from typing import List

from django.db.models import QuerySet

from base_api.interface_frontend import QueryObject, ItemDraftFrontend
from record.models import ItemVersionRecord
from tools.base_tools import filter_to_two_part
from tools.global_const import item_id
from django.core.exceptions import ObjectDoesNotExist


class ItemHistory:
    def __init__(self, user_id: item_id, query_object: QueryObject, version: str = None, version_max: int = 20):
        self.history_set: QuerySet = ItemVersionRecord.objects.filter(SourceId=query_object.id,
                                                                      SourceType=query_object.type)
        self.user_id = user_id
        self.item_query_object = query_object
        if self.history_set.count() == 0:
            self.is_create = True
            version_id = 0
            self.current_record: ItemVersionRecord = self._record_init(version_id)
        elif not version and self.history_set.count() < version_max:
            self.is_create = True
            version_id = self.history_set.latest('UpdateTime').VersionId + 1
            self.current_record = self._record_init(version_id)
        elif version:
            self.is_create = False
            version_id = int(version)
            self.current_record = self.history_set.get(VersionId=version_id)
        else:
            self.is_create = False
            oldest_record = self.history_set.filter(IsUsed=False).first()
            if not oldest_record:
                oldest_record = self.history_set.filter(DontClear=False).earliest('UpdateTime')
                if not oldest_record:
                    raise ObjectDoesNotExist
            self.current_record = oldest_record

    def _record_init(self, version_id):
        return ItemVersionRecord(
            SourceId=self.item_query_object.id,
            SourceType=self.item_query_object.type,
            SourceLabel=self.item_query_object.pLabel,
            VersionId=version_id,
            CreateUser=self.user_id
        )

    def record_update(self,
                      content: ItemDraftFrontend,
                      create_type: str,
                      is_auto: bool = False,
                      is_draft: bool = False):
        self.current_record.Content = content.Content
        self.current_record.Name = content.Name
        self.current_record.IsUsed = True
        self.current_record.IsDraft = is_draft
        self.current_record.IsAuto = is_auto
        self.current_record.CreateType = create_type
        return self

    def record_from_item(self, content: dict, name: str):
        self.current_record.Content = content
        self.current_record.Name = name
        self.current_record.IsUsed = True
        self.current_record.IsDraft = False
        self.current_record.IsAuto = True
        self.current_record.CreateType = 'SYSTEM'
        return self

    def save(self):
        self.current_record.save()

    @staticmethod
    def bulk_save(model_list):
        remote_list, new_item_list = filter_to_two_part(model_list, lambda model: not model.is_create)
        remote_list = [model.current_record for model in remote_list]
        new_item_list = [model.current_record for model in new_item_list]
        ItemVersionRecord.objects.bulk_create(new_item_list)
        ItemVersionRecord.objects.bulk_update(remote_list, fields=ItemVersionRecord.update_fields())
        return {model.current_record.SourceId: model.current_record.VersionId for model in model_list}
