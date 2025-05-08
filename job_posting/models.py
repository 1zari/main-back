import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from user.models import CommonUser
from utils.models import TimestampModel


class JobPosting(TimestampModel):
    """
    공고글 모델
    """

    job_posting_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )  # 공고글 ID
    job_posting_title = models.CharField(max_length=50)  # 공고글 제목
    address = models.CharField(
        max_length=50, default="근무지 전체 주소"
    )  # 근무지주소
    city = models.CharField(max_length=10, default="시,도")  # 시,도
    district = models.CharField(max_length=10, default="시,군,구")  # 시,군,구
    town = models.CharField(max_length=10, default="읍,면,동")  # 읍,면,동
    location = models.PointField(
        verbose_name="근무지 좌표", srid=4326
    )  # 근무지 위치 x,y (위도,경도)
    work_time_start = models.TimeField()  # 근무 시작 시간
    work_time_end = models.TimeField()  # 근무 종료 시간
    posting_type = models.CharField(max_length=10)  # 고용글 종류
    employment_type = models.CharField(max_length=10)  # 고용 형태
    work_experience = models.CharField(max_length=10)  # 경력 여부
    job_keyword_main = models.CharField(max_length=20)  # 직종 대분류
    job_keyword_sub = ArrayField(
        models.CharField(max_length=50), blank=True, default=list
    )  # 직종 중분류
    number_of_positions = models.IntegerField()  # 채용 인원 수
    company_id = models.ForeignKey(
        "user.CompanyInfo",
        on_delete=models.CASCADE,
        related_name="job_postings",
        verbose_name="매니저 ID",
    )  # 등록 매니저 ID
    education = models.CharField(max_length=20)  # 학력
    deadline = models.DateField()  # 지원 마감일
    time_discussion = models.BooleanField()  # 시간 협의 가능
    day_discussion = models.BooleanField()  # 요일 협의 가능
    work_day = ArrayField(
        models.CharField(max_length=20), blank=True, default=list
    )  # 근무 요일
    salary_type = models.CharField(max_length=10)  # 급여 유형
    salary = models.IntegerField()  # 급여 금액
    summary = models.CharField(max_length=50)  # 공고 요약
    content = models.TextField(null=True)  # 공고 상세 내용

    def __str__(self):
        return self.job_posting_title


class JobPostingBookmark(TimestampModel):
    """
    유저 - 공고 북마크 조인 테이블
    """

    user = models.ForeignKey(
        "user.CommonUser",
        on_delete=models.CASCADE,
        related_name="bookmarked_postings",
    )
    job_posting = models.ForeignKey(
        "job_posting.JobPosting",
        on_delete=models.CASCADE,
        related_name="bookmarked_users",
    )

    class Meta:
        unique_together = ("user", "job_posting")  # 북마크 중복 방지
        verbose_name = "공고 북마크"
        verbose_name_plural = "공고 북마크 목록"

    def __str__(self):
        return f"{self.user}_{self.job_posting.job_posting_title}"
