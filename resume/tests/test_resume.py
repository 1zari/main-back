import json
from gc import get_objects

import pytest
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.test.client import Client

from resume.models import CareerInfo, Certification, Resume
from user.models import CommonUser, UserInfo


@pytest.fixture
def mock_common_user(db):
    user = CommonUser.objects.create(
        email="test@test.com",
        password="1q2w3e4r",
        join_type="nomal",
        is_active=True,
        last_login=None,
    )
    return user


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


@pytest.fixture
def client():
    """Django 테스트 Client 객체 생성"""
    return Client()


@pytest.mark.django_db
def test_my_resume_list_view_get(client, mock_user, mock_common_user):

    # 이력서 샘플 생성
    resume = Resume.objects.create(
        user=mock_user,
        resume_title="Test Resume",
        job_category="IT",
        education_level="Bachelor",
        school_name="Test University",
        education_state="Graduated",
        introduce="Test introduction",
    )

    url = "/api/resume/"

    client.force_login(mock_common_user)

    response = client.get(url, content_type="application_json")

    print(response.content)
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "resume_list" in data
    assert len(data["resume_list"]) >= 1


@pytest.mark.django_db
def test_my_resume_list_view_post_success(client, mock_user, mock_common_user):
    """
    MyResumeListView의 POST 메서드 성공 테스트 (새 이력서 등록)
    """
    # 실제 URLConf에 맞게 수정하세요!
    url = "/api/resume/"

    post_data = {
        "resume_title": "My First Resume",
        "job_category": "개발자",
        "education_level": "University",
        "school_name": "서울대",
        "education_state": "Graduated",
        "introduce": "A brief introduction about myself.",
        "career_list": [
            {
                "company_name": "Tech Corp",
                "position": "백엔드",
                "employment_period_start": "2022-01-01",
                "employment_period_end": "2023-12-31",
            },
            {
                "company_name": "Startup ABC",
                "position": "Intern",
                "employment_period_start": "2021-07-01",
                "employment_period_end": "2021-12-31",
            },
        ],
        "certification_list": [
            {
                "certification_name": "OCJP",
                "issuing_organization": "Oracle",
                "date_acquired": "2022-03-15",
            },
            {
                "certification_name": "TOEIC",
                "issuing_organization": "ETS",
                "date_acquired": "2021-09-01",
            },
        ],
    }

    # 로그인: CommonUser를 인증 주체로 사용 (settings.AUTH_USER_MODEL이 CommonUser여야 함)
    client.force_login(mock_common_user)

    response = client.post(
        url, data=json.dumps(post_data), content_type="application/json"
    )

    print(response.status_code)
    print(response.content)

    # 1. 응답 상태 코드
    assert response.status_code == 201

    # 2. 응답 Content-Type
    assert response.get("content-type") == "application/json"

    # 3. 응답 본문 파싱
    response_data = json.loads(response.content)

    # 4. 응답 데이터 구조 및 내용 검증
    assert "message" in response_data
    assert response_data["message"] == "Resume created successfully"
    assert "resume" in response_data
    created_resume = response_data["resume"]
    assert "resume_id" in created_resume
    assert created_resume["resume_title"] == post_data["resume_title"]
    assert created_resume["job_category"] == post_data["job_category"]
    assert created_resume["education_level"] == post_data["education_level"]

    # 5. 경력/자격증 리스트 검증
    assert "career_list" in created_resume
    assert isinstance(created_resume["career_list"], list)
    assert len(created_resume["career_list"]) == len(post_data["career_list"])
    if created_resume["career_list"]:
        assert "company_name" in created_resume["career_list"][0]

    assert "certification_list" in created_resume
    assert isinstance(created_resume["certification_list"], list)
    assert len(created_resume["certification_list"]) == len(
        post_data["certification_list"]
    )
    if created_resume["certification_list"]:
        assert "certification_name" in created_resume["certification_list"][0]

    # 6. DB에 실제로 저장되었는지 확인
    assert Resume.objects.filter(user=mock_user).count() == 1
    saved_resume = Resume.objects.get(user=mock_user)
    assert str(saved_resume.resume_id) == created_resume["resume_id"]
    assert saved_resume.resume_title == post_data["resume_title"]

    saved_careers = CareerInfo.objects.filter(resume=saved_resume)
    assert saved_careers.count() == len(post_data["career_list"])
    assert saved_careers.filter(
        company_name="Tech Corp", position="백엔드"
    ).exists()
    assert saved_careers.filter(
        company_name="Startup ABC", position="Intern"
    ).exists()

    saved_certifications = Certification.objects.filter(resume=saved_resume)
    assert saved_certifications.count() == len(post_data["certification_list"])
    assert saved_certifications.filter(
        certification_name="OCJP", issuing_organization="Oracle"
    ).exists()
    assert saved_certifications.filter(
        certification_name="TOEIC", issuing_organization="ETS"
    ).exists()


@pytest.mark.django_db
def test_my_resume_detail_get_success(client, mock_user, mock_common_user):
    """
    이력서 상세 조회
    """
    # 이력서 샘플 생성
    resume = Resume.objects.create(
        user=mock_user,
        resume_title="Test Resume",
        job_category="IT",
        education_level="Bachelor",
        school_name="Test University",
        education_state="Graduated",
        introduce="Test introduction",
    )

    url = f"/api/resume/{resume.resume_id}/"
    client.force_login(mock_common_user)

    response = client.get(url, content_type="application/json")
    get_data = json.loads(response.content)["resume"]

    assert response.status_code == 200
    data = json.loads(response.content)
    assert "resume" in data
    assert len(data["resume"]) >= 1
    assert get_data["resume_title"] == resume.resume_title
    assert get_data["job_category"] == resume.job_category
    assert get_data["user"]["user_id"] == str(resume.user.user_id)


@pytest.mark.django_db
def test_my_resume_patch_detail_success(client, mock_user, mock_common_user):
    """
    patch 테스트
    """
    resume = Resume.objects.create(
        user=mock_user,
        resume_title="Test Resume",
        job_category="IT",
        education_level="Bachelor",
        school_name="Test University",
        education_state="Graduated",
        introduce="Test introduction",
    )

    patch_data = {
        "resume_id": str(resume.resume_id),
        "job_category": "아이티",
        "resume_title": "바뀐 타이틀",
        "school_name": "경희대",
        "career_list": [
            {
                "company_name": "경희의료원",
                "position": "잡부",
                "employment_period_start": "1996-02-26",
                "employment_period_end": None,
            }
        ],
        "certification_list": [
            {
                "certification_name": "정보처리기사",
                "issuing_organization": "우리집",
                "date_acquired": "2025-04-15",
            }
        ],
    }

    url = f"/api/resume/{resume.resume_id}/"

    client.force_login(mock_common_user)

    response = client.patch(
        url, json.dumps(patch_data), content_type="application/json"
    )
    print(response.content)
    get_data = json.loads(response.content)["resume"]
    assert get_data["resume_id"] == str(resume.resume_id)
    assert get_data["resume_title"] == patch_data["resume_title"]
    assert get_data["career_list"][0]["company_name"] == "경희의료원"


@pytest.mark.django_db
def test_my_resume_delete_success(client, mock_user, mock_common_user):
    resume = Resume.objects.create(
        user=mock_user,
        resume_title="Test Resume",
        job_category="IT",
        education_level="Bachelor",
        school_name="Test University",
        education_state="Graduated",
        introduce="Test introduction",
    )

    url = f"/api/resume/{resume.resume_id}/"

    client.force_login(mock_common_user)

    response = client.delete(url, content_type="application/json")
    print(response.content)
    response_data = json.loads(response.content)
    assert response_data["message"] == "Successfully deleted resume"

    # db에 조회 되는지 확인
    with pytest.raises(Http404):
        get_object_or_404(Resume, pk=resume.resume_id)
