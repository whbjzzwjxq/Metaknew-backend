from record.models import ItemVersionRecord
from tools.global_const import item_id
from django.core.exceptions import ObjectDoesNotExist


class History:
    def __init__(self, user_id: item_id, query_object, version_max=20):
        self.history_set = ItemVersionRecord.objects.filter(
            SourceId=query_object['_id'], SourceType=query_object['_type'])
        self.user_id = user_id
        self.item_query_object = query_object
        self.version_max = version_max
        self.current_record = None
        if not self.history_set:
            self.current = -1
        else:
            self.current = self.history_set.latest('CreateTime').VersionId

    def add_record(self, content, name, create_type):
        if not self.history_set or self.history_set.__len__() < self.version_max:
            version_id = self.current + 1
            new_record = ItemVersionRecord(
                SourceId=self.item_query_object['_id'],
                SourceType=self.item_query_object['_type'],
                SourceLabel=self.item_query_object['_label'],
                VersionId=version_id
            )
            self.current_record = new_record
        else:
            # 先找被删除的
            oldest_record = self.history_set.filter(IsUsed=False).first()
            if not oldest_record:
                oldest_record = self.history_set.filter(DontClear=False).earliest('CreateTime')
                if not oldest_record:
                    raise ObjectDoesNotExist
            self.current_record = oldest_record
        self.current_record.CreateUser = self.user_id,
        self.current_record.Content = content
        self.current_record.Name = name
        self.current_record.IsUsed = True
        self.current_record.CreateType = create_type

    def save(self):
        self.current_record.save()
