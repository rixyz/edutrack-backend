from django.urls import path

from users.views import (
    RequestPasswordResetView,
    ResetPasswordView,
    StudentAPIView,
    StudentBySemesterView,
    TeacherAPIView,
    UserAPIView,
    UserInfoView,
    UserSearchView,
)

app_name = "users"

urlpatterns = [
    path("users/", UserAPIView.as_view(), name="user-list"),
    path("users/search/", UserSearchView.as_view(), name="user-search"),
    path(
        "users/<int:pk>/",
        UserInfoView.as_view(),
        name="assignment-submission-grade",
    ),
    path("students/", StudentAPIView.as_view(), name="student-list"),
    path(
        "students/<int:semester>", StudentBySemesterView.as_view(), name="student-list"
    ),
    path("teachers/", TeacherAPIView.as_view(), name="teacher-list"),
    path("user/info/", UserInfoView.as_view(), name="user-self-info"),
    path("password_reset/", RequestPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset_confirm/<str:uidb64>/<str:token>/",
        ResetPasswordView.as_view(),
        name="password_reset_confirm",
    ),
]
