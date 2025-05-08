import uuid

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

from job_posting.models import JobPosting
from user.models import CommonUser, CompanyInfo


@pytest.mark.django_db
def test_job_posting_creation():
    """
    JobPosting model test
    """
    # 1. CommonUser 생성
    common_user = CommonUser.objects.create(
        email="joptest@test.com",
        password="test",
        join_type="company",
        last_login=timezone.now(),
    )

    # 2. CompanyInfo 생성
    company = CompanyInfo.objects.create(
        common_user=common_user,
        company_name="테스트회사",
        establishment=timezone.now().date(),
        company_address="서울특별시 강남구 테헤란로",
        business_registration_number="02-123-4567",
        company_introduction="테스트 회사 입니다.",
        certificate_image="https://example.com/certificate.jpg",
        ceo_name="잡테스",
        manager_name="김잡스",
        manager_phone_number="010-1234-5678",
        manager_email="manager@example.com",
        is_staff=True,
    )
    common_user.is_active = True
    common_user.save()

    # 3. JobPosting 생성
    posting = JobPosting.objects.create(
        job_posting_title="백엔드 개발자 모집",
        location=Point(127.0276, 37.4979, srid=5179),  # (경도, 위도)
        work_time_start=timezone.now(),
        work_time_end=timezone.now() + timezone.timedelta(hours=8),
        posting_type="계약직",
        employment_type="경력무관",
        job_keyword_main="IT・기술",
        job_keyword_sub="프로그래머",
        number_of_positions=2,
        company_id=company,
        education="고졸",
        deadline=timezone.now() + timezone.timedelta(days=10),
        time_discussion=True,
        day_discussion=True,
        work_day=["월", "화", "수", "목", "금"],
        salary_type="월급",
        salary=3500000,
        summary="주니어 백엔드 개발자 채용",
        content="REST API 개발 및 유지보수 담당.",
    )

    # 4. 테스트
    assert isinstance(posting.job_posting_id, uuid.UUID)
    assert posting.company_id == company
    assert posting.salary == 3500000
    assert "프로그래머" in posting.job_keyword_sub
    assert posting.work_day == ["월", "화", "수", "목", "금"]
    assert posting.location.x == 127.0276  # 경도
    assert posting.location.y == 37.4979  # 위도
    assert str(posting) == "백엔드 개발자 모집"
    assert posting.work_time_end > posting.work_time_start
    assert posting.deadline > timezone.now()
    assert posting.salary > 0
    assert posting.number_of_positions > 0
    assert len(posting.work_day) == 5
