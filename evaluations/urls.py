from django.urls import path

from evaluations.views import (
    PredictionsView,
    StudentResultsView,
    SubjectPredictionsView,
    TeacherStudentView,
)

urlpatterns = [
    path(
        "predictions/<int:student_id>/",
        PredictionsView.as_view(),
        name="student_predictions",
    ),
    path(
        "predictions/<int:student_id>/subject/",
        SubjectPredictionsView.as_view(),
        name="subject_predictions",
    ),
    path(
        "predictions/<int:student_id>/subject/<int:subject_id>/",
        SubjectPredictionsView.as_view(),
        name="specific_subject_predictions",
    ),
    path(
        "predictions/teacher/",
        TeacherStudentView.as_view(),
        name="specific_subject_predictions",
    ),
    path(
        "result/<int:student_id>/", StudentResultsView.as_view(), name="student-results"
    ),
]
