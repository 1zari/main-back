import json

import pytest
from django.contrib.gis.geos import Point
from django.test.client import Client
from django.utils import timezone

from job_posting.models import JobPosting
from resume.models import CareerInfo, Certification, Resume, Submission
from resume.schemas import CareerInfoModel, CertificationInfoModel
from user.models import CommonUser, CompanyInfo, UserInfo
from user.services.token import create_access_token


# mock 일반 common_user 생성
@pytest.fixture
def mock_common_user(db):
    user = CommonUser.objects.create(
        email="test@test.com",
        password="1q2w3e4r",
        join_type="normal",
        is_active=True,
        last_login=None,
    )
    return user


# mock 기업 common_user 생성
@pytest.fixture
def mock_common_company_user(db):
    user = CommonUser.objects.create(
        email="company@test.com",
        password="1q2w3e4r",
        join_type="company",
        is_active=True,
        last_login=None,
    )
    return user


# mock 일반 유저 생성
@pytest.fixture
def mock_user(db, mock_common_user):
    user_info = UserInfo.objects.create(
        common_user=mock_common_user,
        name="test_name",
        phone_number="010123123",
        gender="male",
        interest=[],
        purpose_subscription=[],
        route=[],
    )
    return user_info


# mock 기업 유저 생성
@pytest.fixture
def mock_company_user(db, mock_common_company_user):
    company_user = CompanyInfo.objects.create(
        common_user=mock_common_company_user,
        company_name="테스트 기업",
        establishment="2024-02-01",
        company_address="인천광역시 미추홀구 주안동",
        business_registration_number="13231321312",
        company_introduction="안녕하세요 테스트 기업입니다.",
        ceo_name="덕배최강짱",
        manager_name="김휘수",
        manager_email="test@treqwe.com",
        manager_phone_number="123123",
    )
    return company_user


# mock 공고 생성
@pytest.fixture
def mock_job_posting(db, mock_company_user):
    p = Point(127.0276, 37.4979)
    p.srid = 4326
    jon_posting = JobPosting.objects.create(
        job_posting_title="백엔드 개발자 모집",
        location=p,  # (경도, 위도)
        work_time_start=timezone.now(),
        work_time_end=timezone.now() + timezone.timedelta(hours=8),
        posting_type="정규직",
        employment_type="경력",
        city="인천광역시",
        district="부평구",
        town="부평동",
        job_keyword_main="개발",
        job_keyword_sub=["백엔드", "Django", "Python"],
        number_of_positions=2,
        company_id=mock_company_user,
        education="대학교 졸업",
        deadline=timezone.now() + timezone.timedelta(days=14),
        time_discussion=True,
        day_discussion=True,
        work_day=["월", "화", "수", "목", "금"],
        salary_type="연봉",
        salary=50000000,
        summary="성장하는 IT기업에서 백엔드 개발자를 찾습니다.",
        content="주요 업무: 백엔드 개발 및 유지보수, REST API 설계, 코드 리뷰 등",
    )
    return jon_posting


# mock 이력서 생성
@pytest.fixture
def mock_resume(db, mock_user):
    return Resume.objects.create(
        user=mock_user,
        resume_title="Test Resume",
        job_category="IT",
        education_level="Bachelor",
        school_name="Test University",
        education_state="Graduated",
        introduce="Test introduction",
    )


# mock 경력 생성
@pytest.fixture
def mock_careers(db, mock_resume):
    careers = [
        CareerInfo.objects.create(
            resume=mock_resume,
            company_name="Tech Corp",
            position="백엔드",
            employment_period_start="2022-01-01",
            employment_period_end="2023-12-31",
        ),
        CareerInfo.objects.create(
            resume=mock_resume,
            company_name="Startup ABC",
            position="Intern",
            employment_period_start="2021-07-01",
            employment_period_end="2021-12-31",
        ),
    ]
    return careers


# mock 자격증 생성
@pytest.fixture
def mock_certifications(db, mock_resume):
    certifications = [
        Certification.objects.create(
            resume=mock_resume,
            certification_name="OCJP",
            issuing_organization="Oracle",
            date_acquired="2022-03-15",
        ),
        Certification.objects.create(
            resume=mock_resume,
            certification_name="TOEIC",
            issuing_organization="ETS",
            date_acquired="2021-09-01",
        ),
    ]
    return certifications


# mock 공고 지원 생성
@pytest.fixture
def mock_submission(
    db,
    mock_user,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_job_posting,
):
    submission = Submission.objects.create(
        job_posting=mock_job_posting,
        user=mock_user,
        snapshot_resume={
            "job_category": mock_resume.job_category,
            "resume_title": mock_resume.resume_title,
            "education_level": mock_resume.education_level,
            "school_name": mock_resume.school_name,
            "education_state": mock_resume.education_state,
            "introduce": mock_resume.introduce,
            "career_list": [
                CareerInfoModel.model_validate(mock_career).model_dump(mode="json") for mock_career in mock_careers
            ],
            "certification_list": [
                CertificationInfoModel.model_validate(mock_certi).model_dump(mode="json")
                for mock_certi in mock_certifications
            ],
        },
        created_at=mock_resume.created_at,
    )
    return submission


@pytest.fixture
def client():
    """Django 테스트 Client 객체 생성"""
    return Client()


@pytest.mark.django_db
def test_submission_list_get_success(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_user,
    mock_common_user,
    mock_job_posting,
    mock_submission,
):
    """
    일반 유저가 자신의 지원 목록 조회
    """
    token = create_access_token(mock_common_user)

    url = "/api/submission/"

    response = client.get(url, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")

    response_data = json.loads(response.content)["submission_list"]
    assert response.status_code == 200
    assert response_data[0]["job_posting"]["company_name"] == mock_submission.job_posting.company_id.company_name


@pytest.mark.django_db
def test_submiison_company_get_list_success(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_common_company_user,
    mock_job_posting,
    mock_submission,
    mock_company_user,
):
    """
    기업 유저가 지원자 목록 조회
    """
    token = create_access_token(mock_common_company_user)

    url = "/api/submission/company/"

    response = client.get(url, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")
    response_data = json.loads(response.content)

    assert response.status_code == 200
    assert response_data["message"] == "Successfully loaded submission_list"
    assert response_data["job_posting_list"][0]["job_posting_id"] == str(mock_job_posting.job_posting_id)
    assert response_data["submission_list"][0]["resume_title"] == mock_resume.resume_title
    assert response_data["submission_list"][0]["job_posting_id"] == str(mock_submission.job_posting.job_posting_id)


@pytest.mark.django_db
def test_update_memo_success(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_user,
    mock_submission,
    mock_job_posting,
    mock_common_user,
):
    """
    memo update 테스트
    """
    token = create_access_token(mock_common_user)

    new_memo = {"memo": "new_memo"}
    url = f"/api/submission/memo/{mock_submission.submission_id}/"

    response = client.patch(url, new_memo, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")
    response_data = json.loads(response.content)
    assert response.status_code == 200
    assert response_data["message"] == "Successfully updated memo"
    assert response_data["memo"] == new_memo["memo"]


@pytest.mark.django_db
def test_delete_memo_success(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_user,
    mock_common_user,
    mock_job_posting,
    mock_submission,
):
    """
    memo 삭제
    """
    token = create_access_token(mock_common_user)

    url = f"/api/submission/memo/{mock_submission.submission_id}/"

    response = client.delete(url, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")

    response_data = json.loads(response.content)

    assert response.status_code == 200
    assert response_data["message"] == "Successfully deleted submission memo"


@pytest.mark.django_db
def test_submission_create_success(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_common_user,
    mock_user,
    mock_job_posting,
):
    """
    공고 지원 api 테스트
    """
    token = create_access_token(mock_common_user)

    url = "/api/submission/"

    post_data = {
        "job_posting_id": mock_job_posting.job_posting_id,
        "resume_id": mock_resume.resume_id,
    }

    response = client.post(url, post_data, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")

    response_data = json.loads(response.content)
    assert response.status_code == 201


@pytest.mark.django_db
def test_submission_company_detail_get_success(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_common_company_user,
    mock_company_user,
    mock_submission,
    mock_job_posting,
):
    """
    기업 유저가 지원자 이력서 상세 조회
    """
    token = create_access_token(mock_common_company_user)

    url = f"/api/submission/company/{mock_submission.submission_id}/"

    response = client.get(url, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")
    response_data = json.loads(response.content)["submission"]

    assert response.status_code == 200
    assert response_data["name"] == mock_submission.user.name
    assert response_data["resume_title"] == mock_submission.snapshot_resume["resume_title"]
    refreshed = Submission.objects.get(submission_id=mock_submission.submission_id)
    # 기업 유저가 이력서 조회 했을 때 읽음 처리 확인
    assert refreshed.is_read is True


@pytest.mark.django_db
def test_get_submission_detail_nomal_user(
    client,
    mock_resume,
    mock_careers,
    mock_certifications,
    mock_common_user,
    mock_user,
    mock_submission,
    mock_job_posting,
    mock_company_user,
):
    token = create_access_token(mock_common_user)

    url = f"/api/submission/{mock_submission.submission_id}/"

    response = client.get(url, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}")
    response_data = json.loads(response.content)

    assert response.status_code == 200
    assert response_data["submission"]["submission_id"] == str(mock_submission.submission_id)
