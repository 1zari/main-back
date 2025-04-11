from uuid import uuid4

from django.db import models
from django.db.models import CASCADE

from user.models import UserInfo
from utils.models import TimestampModel


# Create your models here.
class Resume(TimestampModel):
    """
    이력서 모델
    """

    resume_id = models.UUIDField(
        "id", primary_key=True, default=uuid4, editable=False, db_index=True
    )
    user_id = models.ForeignKey(
        "user.UserInfo", on_delete=CASCADE, related_name="resumes"
    )
    education = models.CharField("학력 사항", max_length=20)  # 학력사항
    introduce = models.TextField(verbose_name="자기소개서")  # 자기소개 글

    def __str__(self):
        return self.resume_id
