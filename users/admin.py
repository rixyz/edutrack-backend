from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from academics.models import TeacherSubject
from users.forms import UserAdminChangeForm, UserAdminCreationForm
from users.models import Student, Teacher, User


# Register your models here.
@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
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
                    "groups",
                    "role",
                ),
            },
        ),
        (_("Dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "role",
    ]
    search_fields = ["first_name", "last_name"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])

    get_groups.short_description = "Groups"


class TeacherSubjectInline(admin.TabularInline):
    """Inline admin configuration for TeacherSubject."""

    model = TeacherSubject
    extra = 1
    verbose_name = "Subject"
    verbose_name_plural = "Subjects"


class TeacherAdmin(admin.ModelAdmin):
    """Customized admin view for Teacher model."""

    inlines = [TeacherSubjectInline]
    list_display = ("__str__", "get_email")

    def get_email(self, obj):
        """Display the user's email in the admin list view."""
        return obj.user.email

    get_email.short_description = "Email"


admin.site.register(Teacher, TeacherAdmin)

admin.site.register(Student)
