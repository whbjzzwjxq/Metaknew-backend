
from celery import Celery
from history import models

app = Celery(__name__, broker='amqp://guest:guest@localhost:5672//')

class history_info:

    @app.task
    def add_history(self, filedata={}):
        history = models.history.objects.create(**filedata)
        return history