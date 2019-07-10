from history import models

class BaseHistory:

    def create(self, data):
        self.data = models.objects.create(**data)
        return self.data