from datetime import date

import pytest

from user.models import CommonUser, CompanyInfo, UserInfo


@pytest.mark.django_db
def test_common_user_creation():
    user = CommonUser.objects.create(
        email="test@example.com",
        password="hashed_pw",
        join_type="normal",
        is_active=True,
    )
    assert user.email == "test@example.com"
    assert user.join_type == "normal"
    assert user.created_at is not None
    assert user.last_login is None
    assert user.is_active is True


@pytest.mark.django_db
def test_user_info_creation():
    user = CommonUser.objects.create(
        email="user@example.com", password="pw", join_type="nomal"
    )
    profile = UserInfo.objects.create(
        common_user=user,
        name="홍길동",
        phone_number="01012345678",
        gender="남성",
        birthday=date(1990, 1, 1),
        interest=["사무", "서비스"],
        purpose_subscription=["일자리", "재취업"],
        route=["네이버", "지인"],
    )
    assert profile.name == "홍길동"
    assert profile.phone_number == "01012345678"


@pytest.mark.django_db
def test_company_info_creation():
    company_user = CommonUser.objects.create(
        email="biz@example.com", password="pw", join_type="company"
    )
    company = CompanyInfo.objects.create(
        common_user=company_user,
        company_name="테스트주식회사",
        establishment=date(2020, 5, 1),
        company_address="서울시 강남구",
        business_registration_number="1234567890",
        company_introduction="이 회사는 좋은 회사입니다.",
        certificate_image="http://example.com/image.jpg",
        ceo_name="대표",
        manager_name="매니저",
        manager_phone_number="01099998888",
        manager_email="manager@example.com",
    )
    assert company.company_name == "테스트주식회사"
    assert company.manager_email == "manager@example.com"
    assert company.ceo_name == "대표"
