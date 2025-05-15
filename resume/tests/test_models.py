import uuid

import pytest
from django.utils import timezone

from resume.models import Resume
from user.models import CommonUser, UserInfo


@pytest.mark.django_db
def test_resume_creation():
    # Given
    common_user = CommonUser.objects.create(
        email="test@example.com",
        password="testpassword",
        join_type="email",
        last_login=timezone.now(),
    )
    user_info = UserInfo.objects.create(
        common_user=common_user,
        name="홍길동",
        phone_number="010-1234-5678",
        gender="male",
        birthday=timezone.now().date(),
    )

    # When
    resume = Resume.objects.create(
        user=user_info,
        education_level="대학교",
        resume_title="테스트이력서",
        school_name="경희대",
        education_state="학사졸업",
        introduce="자기소개 내용입니다.",
    )

    # Then
    assert isinstance(resume.resume_id, uuid.UUID)
    assert resume.user == user_info
    assert resume.resume_title == "테스트이력서"
    assert resume.education_level == "대학교"
    assert resume.school_name == "경희대"
    assert resume.education_state == "학사졸업"
    assert resume.introduce == "자기소개 내용입니다."
    assert resume.created_at is not None
    assert resume.updated_at is not None


@pytest.mark.django_db
def test_resume_deletion():
    # Given
    common_user = CommonUser.objects.create(
        email="test@example.com",
        password="testpassword",
        join_type="email",
        last_login=timezone.now(),
    )
    user_info = UserInfo.objects.create(
        common_user=common_user,
        name="홍길동",
        phone_number="010-1234-5678",
        gender="male",
        birthday=timezone.now().date(),
    )

    # When
    resume = Resume.objects.create(
        user=user_info,
        resume_title="테스트 이력서",
        education_level="대학교",
        school_name="경희대",
        education_state="학사졸업",
        introduce="자기소개 내용입니다.",
    )
    resume_id = resume.resume_id
    resume.delete()

    # Then
    with pytest.raises(Resume.DoesNotExist):
        Resume.objects.get(resume_id=resume_id)

    # 유저 정보 남아있는지 확인
    assert CommonUser.objects.get(common_user_id=common_user.common_user_id)
    assert UserInfo.objects.get(user_id=user_info.user_id)


@pytest.mark.django_db
def test_resume_str_method():
    # Given
    common_user = CommonUser.objects.create(
        email="test2@example.com",
        password="testpassword",
        join_type="email",
        last_login=timezone.now(),
    )
    user_info = UserInfo.objects.create(
        common_user=common_user,
        name="김철수",
        phone_number="010-9876-5432",
        gender="male",
        birthday=timezone.now().date(),
    )

    resume = Resume.objects.create(
        user=user_info,
        education_level="대학교",
        resume_title="테스트 이력서",
        school_name="경희대",
        education_state="학사졸업",
        introduce="자기소개 내용입니다.",
    )

    # Then
    assert str(resume)  # __str__이 정상 동작하는지 확인
    assert isinstance(resume.resume_id, uuid.UUID)
