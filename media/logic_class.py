from media.models import MediaNode

class BaseMedia:

    def __init__(self):
        self.Media = MediaNode()

    def create(self, data):
        self.Media = MediaNode.objects.create(**data)
        return self