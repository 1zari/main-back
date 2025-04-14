from uuid import uuid4

from django.db import models
from django.db.models import CASCADE
from django.db.models.manager import Manager

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
        return str(self.resume_id)

    objects = Manager()


class CareerInfo(TimestampModel):
    """
    경력사항 모델
    """

    career_info_id = models.UUIDField(
        "id", primary_key=True, default=uuid4, editable=False
    )
    resume = models.ForeignKey(
        "Resume", on_delete=CASCADE, related_name="careers"
    )
    company_name = models.CharField("근무 회사 이름", max_length=20)
    position = models.CharField("근무 직책", max_length=20)
    employment_period_start = models.DateField("입사일")
    employment_period_end = models.DateField("퇴사일", null=True)

    objects = Manager()

    def __str__(self):
        return str(self.career_info_id)
