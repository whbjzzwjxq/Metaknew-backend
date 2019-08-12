from record.models import WarnRecord, ErrorRecord, SourceAddRecord, NodeVersionRecord

warn_type = []


class IdGenerationError(BaseException):
    # todo id 生成异常 level: 2
    pass


class ObjectAlreadyExist(BaseException):
    pass


def error_check(_func):
    def wrapped(self, node):
        try:
            result = _func(self, node)
            return result
        except Exception as e:
            name = type(e).__name__
            EWRecord.add_error_record(user=self.user,
                                      source_id=self._id,
                                      source_label=self.__name__,
                                      data=node,
                                      bug_type=name)
            return None
            # todo 消息队列 level: 1

    return wrapped


def field_check(_func):
    def wrapped(self, field, new_prop, old_prop):
        if isinstance(new_prop, str) and len(new_prop) > 1024:
            self.warn.WarnContent.append({"field": field, "warn_type": "toolong_str"})

        if isinstance(new_prop, list) and len(new_prop) > 128:
            self.warn.WarnContent.append({"field": field, "warn_type": "toolong_list"})

        if isinstance(new_prop, dict) and len(new_prop) > 128:
            self.warn.WarnContent.append({"field": field, "warn_type": "toolong_dict"})

        if not bool(new_prop):
            self.warn.WarnContent.append({"field": field, "warn_type": "empty_prop"})

        # 这里主要是针对JSONField 和 ArrayField
        if type(new_prop) != type(old_prop):
            self.warn.WarnContent.append({"field": field, "warn_type": "error_type"})
        return _func(self, field, new_prop, old_prop)

    return wrapped


class EWRecord:

    def __init__(self):
        self.record = SourceAddRecord.objects.all()

    def query_by_criteria(self, criteria_query):
        assert criteria_query["source_type"] == "AddRecord"
        if criteria_query["labels"] is not []:
            for label in criteria_query["labels"]:
                self.query_by_status(label)

        if criteria_query["props"] is not {}:
            for key, value in criteria_query["props"].items():
                self.query_by_props(key=key, value=value)
        limit = criteria_query["limit"]
        return self.record[:limit]

    def query_by_status(self, label):
        self.record = self.record.filter({label: True})
        return self

    def query_by_props(self, key, value):
        self.record = self.record.filter({key: value})
        return self

    @staticmethod
    def add_error_record(user, source_id, source_label, data, bug_type):
        record = ErrorRecord(
            SourceId=source_id,
            SourceLabel=source_label,
            CreateUser=user,
            OriginData=data,
            BugType=bug_type)
        record.save()
        # todo 消息队列 level: 1
        return record

    @staticmethod
    def add_warn_record(user, source_id, source_label, content):
        record = WarnRecord(
            SourceId=source_id,
            SourceLabel=source_label,
            CreateUser=user,
            WarnContent=content
        )
        return record

    @staticmethod
    def bulk_save_warn_record(records):
        result = WarnRecord.objects.bulk_create(records)
        return result


class History:

    @staticmethod
    def bulk_save_node_history(records):
        result = NodeVersionRecord.objects.bulk_create(records)
        return result
