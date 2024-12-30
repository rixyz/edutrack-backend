from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget
from unfold.admin import ModelAdmin

from academics.models import Subject
from evaluations.models import StudentPerformanceMetrics
from users.models import Student


class StudentPerformanceMetricsResource(resources.ModelResource):
    student = fields.Field(
        column_name="student_email",
        attribute="student",
        widget=ForeignKeyWidget(Student, "user__email"),
    )
    subject = fields.Field(
        column_name="subject_code",
        attribute="subject",
        widget=ForeignKeyWidget(Subject, "code"),
    )

    class Meta:
        model = StudentPerformanceMetrics
        fields = (
            "student",
            "subject",
            "attendance_rate",
            "assignment_completion_rate",
            "average_assignment_score",
            "mid_term_grade",
        )
        import_id_fields = ("student", "subject")
        skip_unchanged = True
        report_skipped = True


@admin.register(StudentPerformanceMetrics)
class StudentPerformanceMetricsAdmin(ImportExportMixin, ModelAdmin):
    resource_class = StudentPerformanceMetricsResource

    list_display = [
        "student",
        "subject",
        "attendance_rate",
        "assignment_completion_rate",
        "average_assignment_score",
        "mid_term_grade",
    ]

    list_filter = [
        "subject",
        "student__semester",
        ("mid_term_grade", admin.EmptyFieldListFilter),
    ]

    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "subject__name",
        "subject__code",
    ]

    ordering = ["student__semester", "subject__code"]
