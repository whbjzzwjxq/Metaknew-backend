from history.models import SourceAddRecord


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
    def add_record(error, warn, source_id, source_type, content):

        record = SourceAddRecord.objects.create(
            Is_Error=error,
            Is_Warn=warn,
            SourceId=source_id,
            SourceType=source_type,
            Content=content)

        return record
