from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from EduTrack.utils import get_or_not_found
from users.models import Student, Teacher, User
from users.serializers import (
    ResetPasswordSerializer,
    StudentSerializer,
    TeacherSerializer,
    UserSerializer,
)
from utils.mail_handler import mail_send

# Create your views here.


class UserAPIView(APIView):
    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Get all users",
        responses={200: UserSerializer(many=True)},
    )
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Create a new user",
        request_body=UserSerializer,
        responses={201: UserSerializer()},
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(APIView):
    """
    API view for searching users.
    """

    serializer_class = UserSerializer

    def get_queryset(self, query):
        """
        Filter users based on search query.
        Searches through email and phone fields.
        """
        return User.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
        ).select_related("role")

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Search users by email or phone",
        manual_parameters=[
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="Search query string",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ],
        responses={200: UserSerializer(many=True)},
    )
    def get(self, request):
        query = request.query_params.get("query", "")
        if not query:
            return Response(
                {
                    "message": "Please provide a search query",
                    "data": [],
                    "status": "no_query",
                    "error": "",
                },
                status=status.HTTP_200_OK,
            )

        users = self.get_queryset(query)
        serializer = self.serializer_class(users, many=True)

        return Response(
            {
                "message": "Users retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


class StudentAPIView(APIView):
    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Get all student profiles",
        responses={200: StudentSerializer(many=True)},
    )
    def get(self, request):
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Create a new student profile",
        request_body=StudentSerializer,
        responses={201: StudentSerializer()},
    )
    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherAPIView(APIView):
    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Get all teacher profiles",
        responses={200: TeacherSerializer(many=True)},
    )
    def get(self, request):
        teachers = Teacher.objects.prefetch_related("user", "subject__subject").all()
        serializer = TeacherSerializer(teachers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Users"],
        operation_description="Create a new teacher profile",
        request_body=TeacherSerializer,
        responses={201: TeacherSerializer()},
    )
    def post(self, request):
        serializer = TeacherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserInfoView(APIView):
    @swagger_auto_schema(
        operation_description="Get teacher details including subjects",
        responses={
            200: TeacherSerializer(),
            403: "Not a teacher",
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        if request.user.is_anonymous:
            return Response(
                {
                    "error": "Unauthorized user",
                    "message": "User is anonymous",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if "pk" in kwargs:
            user: User = get_or_not_found(User.objects.all(), pk=kwargs.get("pk"))
        else:
            user: User = request.user

        if user.is_teacher():
            profile = user.teacher_profile
            teacher = Teacher.objects.prefetch_related("subject__subject").get(
                id=profile.id
            )

            serializer = TeacherSerializer(teacher)
            return Response(
                {
                    "message": "Teacher details retrieved successfully",
                    "data": serializer.data,
                    "status": "data_retrieved",
                },
                status=status.HTTP_200_OK,
            )

        elif user.is_student():
            profile = user.student_profile
            student = get_or_not_found(Student.objects.all(), pk=profile.id)

            serializer = StudentSerializer(student)
            return Response(
                {
                    "message": "Student details retrieved successfully",
                    "data": serializer.data,
                    "status": "data_retrieved",
                },
                status=status.HTTP_200_OK,
            )
        else:
            serializer = UserSerializer(user)
            return Response(
                {
                    "message": "User details retrieved successfully",
                    "data": serializer.data,
                    "status": "data_retrieved",
                },
                status=status.HTTP_200_OK,
            )


class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if email:
            try:
                user = get_or_not_found(User.objects.all(), email=email)
                reset_url = user.get_password_reset_url()
                mail_send(user.email, "Link to reset password", reset_url)
                return Response(
                    {
                        "message": "Password reset link has been sent to your email",
                    },
                    status=status.HTTP_200_OK,
                )
            except User.DoesNotExist:
                return Response(
                    {"message": "Password reset link has been sent to your email"},
                    status=status.HTTP_200_OK,
                )
        return Response(
            {"error": "Email is required", "message": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResetPasswordView(APIView):
    def post(self, request, uidb64, token):
        serializer = ResetPasswordSerializer(
            data=request.data, context={"uid": uidb64, "token": token}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password has been reset successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
