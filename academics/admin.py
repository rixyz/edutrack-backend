from django.contrib import admin
from unfold.admin import TabularInline

from academics.models import Assignment, AssignmentSubmission, Course, Lesson, Subject
from utils.admin_import_export import ImportExportBase


@admin.register(Subject)
class SubjectAdmin(ImportExportBase):
    list_display = [
        "name",
        "code",
        "semester",
        "get_teacher_count",
        "get_student_count",
    ]
    list_filter = ["semester"]
    search_fields = ["name", "code"]
    ordering = ["semester", "code"]

    def get_teacher_count(self, obj):
        return obj.teacher.count()

    get_teacher_count.short_description = "Teachers"

    def get_student_count(self, obj):
        return obj.studentperformancemetrics_set.count()

    get_student_count.short_description = "Students"


class LessonInline(TabularInline):
    model = Lesson
    extra = 1
    ordering = ["order"]


@admin.register(Course)
class CourseAdmin(ImportExportBase):
    list_display = [
        "title",
        "subject",
        "type",
        "teacher",
        "duration_formatted",
        "created_at",
    ]
    list_filter = ["subject", "type", "teacher"]
    search_fields = ["title", "description"]
    inlines = [LessonInline]
    date_hierarchy = "created_at"


@admin.register(Assignment)
class AssignmentAdmin(ImportExportBase):
    list_display = [
        "title",
        "subject",
        "due_date",
        "max_score",
        "created_by",
        "get_submission_count",
    ]
    list_filter = ["subject", "created_by", "due_date"]
    search_fields = ["title", "description"]
    date_hierarchy = "due_date"

    def get_submission_count(self, obj):
        return obj.submissions.count()

    get_submission_count.short_description = "Submissions"


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(ImportExportBase):
    list_display = [
        "assignment",
        "student",
        "score",
        "created_at",
        "get_on_time_status",
    ]
    list_filter = [
        "assignment__subject",
        "student__semester",
        "created_at",
    ]
    search_fields = [
        "student__user__first_name",
        "student__user__last_name",
        "assignment__title",
    ]
    date_hierarchy = "created_at"

    def get_on_time_status(self, obj):
        return obj.created_at <= obj.assignment.due_date

    get_on_time_status.short_description = "Submitted On Time"
    get_on_time_status.boolean = True
