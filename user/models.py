import random
import string
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.postgres.fields import ArrayField
from django.db import models

from utils.models import TimestampModel


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def make_random_password(self, length=8):
        """랜덤한 비밀번호를 생성하는 함수"""
        characters = string.ascii_letters + string.digits + string.punctuation
        random_password = "".join(
            random.choice(characters) for i in range(length)
        )
        return random_password

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)


class CommonUser(AbstractBaseUser, PermissionsMixin, TimestampModel):
    """유저 공통 정보 모델 (로그인/비밀번호 등)"""

    # 회원 식별자
    common_user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    # 회원 이메일
    email = models.EmailField(max_length=50, unique=True)
    # 회원 비밀번호
    password = models.CharField(max_length=255)
    # 회원 유형
    join_type = models.CharField(max_length=10)
    # 마지막 로그인 시각
    last_login = models.DateTimeField(null=True, blank=True)
    # 활성 상태 여부
    is_active = models.BooleanField(default=False)
    # 관리자 권한 여부
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.email


class UserInfo(TimestampModel):
    """일반 사용자 상세 정보 모델"""

    # 일반 사용자 식별자
    user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    # 공통 유저 정보 참조
    common_user = models.OneToOneField(CommonUser, on_delete=models.CASCADE)
    # 일반 사용자 이름
    name = models.CharField(max_length=30)
    # 일반 사용자 전화번호
    phone_number = models.CharField(max_length=20, unique=True)
    # 일반 사용자 성별
    gender = models.CharField(max_length=10)
    # 일반 사용자 생년월일
    birthday = models.DateField(null=True, blank=True)

    # 관심 분야
    interest = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )
    # 가입 목적
    purpose_subscription = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )
    # 유입 경로
    route = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.common_user.email})"


class CompanyInfo(TimestampModel):
    """기업 사용자 상세 정보 모델"""

    # 기업 사용자 식별자
    company_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    # 공통 유저 정보 참조
    common_user = models.OneToOneField(CommonUser, on_delete=models.CASCADE)

    # 회사명
    company_name = models.CharField(max_length=50)
    # 회사 설립일
    establishment = models.DateField()
    # 회사 주소
    company_address = models.CharField(max_length=100)
    # 사업자 등록 번호
    business_registration_number = models.CharField(max_length=20)
    # 회사 소개
    company_introduction = models.TextField()
    # 사업자 등록증 이미지
    certificate_image = models.URLField(null=True, blank=True)
    # 회사 로고 이미지
    company_logo = models.URLField(null=True, blank=True)
    # 대표 이름
    ceo_name = models.CharField(max_length=20)
    # 담당자 이름
    manager_name = models.CharField(max_length=30)
    # 담당자 연락처
    manager_phone_number = models.CharField(max_length=30)
    # 담당자 이메일
    manager_email = models.EmailField(max_length=50)

    def __str__(self):
        return self.company_name
