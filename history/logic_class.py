from history.models import WarnRecord, ErrorRecord, SourceAddRecord, BugType


class AddRecord:

    def __init__(self):
        self.record = SourceAddRecord.objects.all()

    def query_by_criteria(self, criteria_query):
        assert criteria_query["source_type"] == 'AddRecord'
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

