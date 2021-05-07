from django.conf import settings
from django.db import models


class SceneID(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sceneids'
    )
    sceneid = models.IntegerField(unique=True)
