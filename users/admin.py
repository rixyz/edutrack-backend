from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from unfold.admin import TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from academics.models import TeacherSubject
from users.models import Student, Teacher, User
from utils.admin_import_export import ImportExportBase


class TeacherSubjectInline(TabularInline):
    model = TeacherSubject
    extra = 1
    verbose_name = "Subject"
    verbose_name_plural = "Subjects"


@admin.register(User)
class UserAdmin(BaseUserAdmin, ImportExportBase):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ("role", "id")

    list_display = [
        "email",
        "first_name",
        "last_name",
    ]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                    "profile_picture",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "role",
                ),
            },
        ),
        (_("Dates"), {"fields": ("date_joined",)}),
    )


@admin.register(Student)
class StudentAdmin(ImportExportBase):
    list_display = [
        "__str__",
        "get_email",
        "get_phone",
        "semester",
        "batch",
        "get_is_active",
    ]
    list_filter = [
        "user__is_active",
        "semester",
        "batch",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone",
        "batch",
    ]
    ordering = ["semester", "batch", "user__first_name"]

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"

    def get_phone(self, obj):
        return obj.user.phone

    get_phone.short_description = "Phone"

    def get_is_active(self, obj):
        return obj.user.is_active

    get_is_active.short_description = "Active"
    get_is_active.boolean = True


@admin.register(Teacher)
class TeacherAdmin(ImportExportBase):
    inlines = [TeacherSubjectInline]
    list_display = [
        "__str__",
        "get_email",
        "get_phone",
        "get_subject_count",
        "get_is_active",
    ]
    list_filter = ["user__is_active"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone",
    ]
    ordering = ["user__first_name", "user__last_name"]

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"

    def get_phone(self, obj):
        return obj.user.phone

    get_phone.short_description = "Phone"

    def get_is_active(self, obj):
        return obj.user.is_active

    get_is_active.short_description = "Active"
    get_is_active.boolean = True

    def get_subject_count(self, obj):
        return obj.subject.count()

    get_subject_count.short_description = "Number of Subjects"


admin.site.unregister(Group)
