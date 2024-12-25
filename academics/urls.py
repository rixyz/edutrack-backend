from django.urls import path

from academics.views import (
    AssignmentDetailView,
    AssignmentStudentView,
    AssignmentTeacherView,
    CourseDetailView,
    CourseStudentView,
    CourseTeacherView,
    LessonTeacherView,
    SubmissionByAssignmentView,
    SubmissionDetailView,
    SubmissionGradeView,
    SubmissionStudentSubmitView,
)

app_name = "academics"
urlpatterns = [
    path("course/teacher/", CourseTeacherView.as_view(), name="course-teacher"),
    path("course/student/", CourseStudentView.as_view(), name="course-student"),
    path("course/<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path("lessons/", LessonTeacherView.as_view(), name="lesson-teacher"),
    path(
        "assignment/teacher/",
        AssignmentTeacherView.as_view(),
        name="assignment-teacher",
    ),
    path(
        "assignment/student/",
        AssignmentStudentView.as_view(),
        name="assignment-student",
    ),
    path(
        "assignment/<int:pk>/", AssignmentDetailView.as_view(), name="assignment-detail"
    ),
    path(
        "assignment/submission/",
        SubmissionStudentSubmitView.as_view(),
        name="assignment-submission-submit",
    ),
    path(
        "assignment/submission/<int:pk>/",
        SubmissionDetailView.as_view(),
        name="assignment-submission-delete",
    ),
    path(
        "assignment/submission/grade/<int:pk>/",
        SubmissionGradeView.as_view(),
        name="assignment-submission-grade",
    ),
    path(
        "assignment/<int:pk>/submission/",
        SubmissionByAssignmentView.as_view(),
        name="assignment-submission",
    ),
]
