import uuid

import pytest
import pytest_django
from django.test import TestCase
from django.utils import timezone

from resume.models import Resume
from user.models import CommonUser, UserInfo


@pytest.mark.django_db
def test_resume_creation():
    # 1. UserInfo 인스턴스 생성 (Resume 모델이 참조)
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
        is_active=True,
    )

    # 2. Resume 인스턴스 생성
    resume = Resume.objects.create(
        user_id=user_info,
        education="대학교 졸업",
        introduce="자기소개 내용입니다.",
    )

    # 3. 생성된 Resume 인스턴스 속성 확인
    assert isinstance(resume.resume_id, uuid.UUID)
    assert resume.user_id == user_info
    assert resume.education == "대학교 졸업"
    assert resume.introduce == "자기소개 내용입니다."
    assert resume.created_at is not None
    assert resume.updated_at is not None


@pytest.mark.django_db
def test_resume_str_method():
    # UserInfo 인스턴스 생성
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
        is_active=True,
    )

    # Resume 인스턴스 생성
    resume = Resume.objects.create(
        user_id=user_info,
        education="전문대 졸업",
        introduce="간단한 자기소개입니다.",
    )

    # __str__ 메서드 반환 값 확인
    assert isinstance(resume.resume_id, uuid.UUID)
