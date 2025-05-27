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

    resume_id = models.UUIDField("id", primary_key=True, default=uuid4, editable=False, db_index=True)
    user = models.ForeignKey("user.UserInfo", on_delete=CASCADE, related_name="resumes")
    job_category = models.CharField(verbose_name="직무 분야", max_length=20, blank=True)  # 직무 분야
    resume_title = models.CharField(verbose_name="이력서 제목", max_length=20)  # 이력서 제목
    education_level = models.CharField(verbose_name="학력 구분", max_length=20)  # 학력 구분
    school_name = models.CharField(verbose_name="학교명", max_length=20)  # 학교명
    education_state = models.CharField(verbose_name="학적", max_length=20)  # 학적 상태

    introduce = models.TextField(verbose_name="자기소개서")  # 자기소개 글

    def __str__(self):
        return self.resume_title

    objects = Manager()


class CareerInfo(TimestampModel):
    """
    경력사항 모델
    """

    career_info_id = models.UUIDField("id", primary_key=True, default=uuid4, editable=False)
    resume = models.ForeignKey("Resume", on_delete=CASCADE, related_name="careers")
    company_name = models.CharField(verbose_name="근무 회사 이름", max_length=20)
    position = models.CharField(verbose_name="직무", max_length=20)
    employment_period_start = models.DateField(verbose_name="입사일")
    employment_period_end = models.DateField(verbose_name="퇴사일", blank=True, null=True)

    objects = Manager()

    def __str__(self):
        return f"{self.company_name} - {self.position}"


class Certification(TimestampModel):
    """
    자격증 정보
    """

    certification_id = models.UUIDField("자격증 아이디", primary_key=True, default=uuid4)
    resume = models.ForeignKey("Resume", on_delete=CASCADE, related_name="certifications")
    certification_name = models.CharField(verbose_name="자격증 이름", max_length=20)
    issuing_organization = models.CharField(verbose_name="발급 기관", max_length=20)
    date_acquired = models.DateField(verbose_name="취득일")

    objects = Manager()

    def __str__(self):
        return self.certification_name


class Submission(TimestampModel):
    """
    지원공고 목록 테이블
    """

    submission_id = models.UUIDField("id", primary_key=True, default=uuid4)
    job_posting = models.ForeignKey(
        "job_posting.JobPosting",
        on_delete=CASCADE,
        related_name="submissions_job_posting",
    )
    user = models.ForeignKey("user.UserInfo", on_delete=CASCADE, related_name="submissions_user")
    snapshot_resume = models.JSONField(verbose_name="지원 시점 이력서 정보")

    memo = models.CharField("지원공고 메모", max_length=50, blank=True, null=True)
    is_read = models.BooleanField("기업 담당자 읽음 여부", default=False)

    objects = Manager()

    def __str__(self):
        return str(self.submission_id)
