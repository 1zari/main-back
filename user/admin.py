from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CommonUser, CompanyInfo, UserInfo


@admin.register(CommonUser)
class CommonUserAdmin(admin.ModelAdmin):
    """CommonUser 모델을 위한 Admin 클래스"""

    list_display = (
        "common_user_id",
        "email",
        "join_type",
        "created_at",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    search_fields = ("email",)
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("created_at",)}),
    )
    readonly_fields = ("common_user_id", "created_at")


@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    """UserInfo 모델을 위한 Admin 클래스"""

    list_display = (
        "user_id",
        "common_user",
        "name",
        "phone_number",
        "gender",
        "birthday",
    )
    search_fields = ("name", "phone_number", "common_user__email")
    list_filter = ("gender",)
    ordering = ("name",)
    # filter_horizontal은 ArrayField에 사용할 수 없으므로 제거
    readonly_fields = ("user_id", "common_user")


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    """CompanyInfo 모델을 위한 Admin 클래스"""

    list_display = (
        "company_id",
        "common_user",
        "company_name",
        "establishment",
        "business_registration_number",
        "ceo_name",
        "manager_name",
        "manager_email",
    )
    search_fields = (
        "company_name",
        "business_registration_number",
        "ceo_name",
        "manager_name",
        "common_user__email",
    )
    list_filter = ("establishment",)
    ordering = ("company_name",)
    readonly_fields = ("company_id", "common_user")
