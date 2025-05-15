from django.db import models
from pydantic import BaseModel


class TimestampModel(models.Model):
    created_at = models.DateTimeField("작성일자", auto_now_add=True)
    updated_at = models.DateTimeField("작성일자", auto_now=True)

    class Meta:
        abstract = True
