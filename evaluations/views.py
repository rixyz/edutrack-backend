from decimal import Decimal
from typing import Any

from django.db.models import QuerySet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Subject
from evaluations.models import StudentPerformanceMetrics, StudentResult
from evaluations.predictions.grade import get_student_predictions_with_explanation
from evaluations.predictions.subject import get_subject_predictions
from users.models import Student, Teacher, User


class PredictionsView(APIView):
    """
    API view for retrieving student predictions.
    """

    @swagger_auto_schema(
        operation_description="Get predictions for a specific student",
        manual_parameters=[
            openapi.Parameter(
                name="student_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description="Unique identifier of the student",
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                "Successful prediction retrieval",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT, additional_properties=True
                ),
            ),
            404: "Student not found",
        },
    )
    def get(self, request, student_id: int) -> Response:
        """
        Retrieve predictions for a specific student.

        Args:
            request (Request): The incoming HTTP request
            student_id (int): The unique identifier of the student

        Returns:
            Response: JSON response containing student predictions
        """
        try:
            predictions = get_student_predictions_with_explanation(student_id)
            return Response(predictions, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SubjectPredictionsView(APIView):
    """
    API view for retrieving student predictions by subject.
    """

    @staticmethod
    def _convert_to_serializable(data: Any) -> Any:
        """
        Recursively convert complex data to JSON-serializable format.

        Args:
            data (Any): Input data to be converted

        Returns:
            Any: JSON-serializable representation of the data
        """
        if isinstance(data, dict):
            return {
                k: SubjectPredictionsView._convert_to_serializable(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [
                SubjectPredictionsView._convert_to_serializable(item) for item in data
            ]
        elif hasattr(data, "name"):
            return data.name
        return data

    @swagger_auto_schema(
        operation_description="Get predictions for a student in a specific subject (optional)",
        manual_parameters=[
            openapi.Parameter(
                name="student_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description="Unique identifier of the student",
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                "Successful subject predictions retrieval",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT, additional_properties=True
                ),
            ),
            404: "Student or Subject not found",
        },
    )
    def get(self, request, student_id: int, subject_id: int | None = None) -> Response:
        """
        Retrieve predictions for a student, optionally filtered by subject.

        Args:
            request (Request): The incoming HTTP request
            student_id (int): The unique identifier of the student
            subject_id (int | None): The unique identifier of the subject.

        Returns:
            Response: JSON response containing subject predictions
        """
        try:
            predictions = get_subject_predictions(student_id, subject_id)
            serializable_predictions = self._convert_to_serializable(predictions)
            return Response(
                {
                    "message": "Student's subject prediction retrieved successfully",
                    "data": serializable_predictions,
                    "status": "data_retrieved",
                },
                status=status.HTTP_200_OK,
            )
        except (Student.DoesNotExist, Subject.DoesNotExist):
            return Response(
                {
                    "error": "Error while fetching Student Information",
                    "message": "Student or Subject not found",
                    "status": "failed",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except LookupError as e:
            return Response(
                {
                    "error": "Error while fetching Student Information",
                    "message": str(e),
                    "status": "failed",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class TeacherStudentView(APIView):
    """
    API view for retrieving students taught by a teacher.
    """

    permission_classes = [IsAuthenticated]

    @staticmethod
    def _convert_to_serializable(data: Any) -> Any:
        """
        Recursively convert complex data to JSON-serializable format.

        Args:
            data (Any): Input data to be converted

        Returns:
            Any: JSON-serializable representation of the data
        """
        if isinstance(data, dict):
            return {
                k: TeacherStudentView._convert_to_serializable(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [TeacherStudentView._convert_to_serializable(item) for item in data]
        elif hasattr(data, "name"):
            return data.name
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        else:
            return str(data)

    @swagger_auto_schema(
        operation_description="Get students for a teacher, optionally filtered by subject",
        manual_parameters=[
            openapi.Parameter(
                name="subject_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Optional subject ID to filter students",
                required=False,
            )
        ],
        responses={
            200: openapi.Response(
                "Successful student retrieval",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT, additional_properties=True
                ),
            ),
            403: "Not a teacher",
            404: "No students found",
        },
    )
    def get(self, request, subject_id: int | None = None) -> Response:
        """
        Retrieve students for a teacher, optionally filtered by subject.

        Args:
            request (Request): The incoming HTTP request
            subject_id (Optional[int], optional): The unique identifier of the subject.

        Returns:
            Response: JSON response containing student details grouped by subjects
        """
        try:
            teacher: Teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return Response(
                {"error": "Access denied. User is not a teacher"},
                status=status.HTTP_403_FORBIDDEN,
            )

        teacher_subjects = Subject.objects.filter(teacher__teacher=teacher)

        if subject_id:
            teacher_subjects = teacher_subjects.filter(id=subject_id)

        if not teacher_subjects.exists():
            return Response(
                {"error": "No subjects found for this teacher"},
                status=status.HTTP_404_NOT_FOUND,
            )

        students_by_subject: dict[str, list[dict[str, Any]]] = {}

        for subject in teacher_subjects:
            students: QuerySet[Student] = Student.objects.filter(
                semester=subject.semester
            ).select_related("user")

            subject_students: list[dict[str, Any]] = []

            for student in students:
                try:
                    performance_metrics: StudentPerformanceMetrics | None = (
                        StudentPerformanceMetrics.objects.filter(
                            student=student, subject=subject
                        ).first()
                    )

                    subject_prediction = get_subject_predictions(
                        student_id=student.user.id, subject_id=subject.id
                    )

                    serializable_prediction = self._convert_to_serializable(
                        subject_prediction.get(subject.name, {})
                    )

                    student_details: dict[str, Any] = {
                        "id": student.user.id,
                        "name": student.user.get_full_name(),
                        "email": student.user.email,
                        "semester": student.semester,
                        "batch": student.batch,
                        "performance_metrics": (
                            {
                                "attendance_rate": performance_metrics.attendance_rate,
                                "assignment_completion_rate": performance_metrics.assignment_completion_rate,  # noqa
                                "average_assignment_score": performance_metrics.average_assignment_score,  # noqa
                            }
                            if performance_metrics
                            else None
                        ),
                        "predictions": serializable_prediction,
                    }

                    subject_students.append(student_details)
                except Exception as e:
                    print(f"Error processing student {student.id}: {str(e)}")

            if subject_students:
                students_by_subject[subject.name] = subject_students

        return Response(
            {
                "message": "Teacher's student prediction retrieved successfully",
                "data": students_by_subject,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


def format_decimal(value: Decimal) -> str:
    """Format decimal to string with 2 decimal places"""
    return f"{float(value):.1f}"  # noqa


class StudentResultsView(APIView):
    """API view for retrieving student results by semester."""

    @swagger_auto_schema(
        operation_description="Get semester-wise results for a specific student",
        manual_parameters=[
            openapi.Parameter(
                name="student_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description="Unique identifier of the student",
                required=True,
            )
        ],
        responses={
            200: openapi.Response(
                "Successful results retrieval",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    additional_properties=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        additional_properties=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "SUBJECT_CODE": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "SUBJECT_NAME": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "CREDIT_HOUR": openapi.Schema(type=openapi.TYPE_STRING),
                                "GPA": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    ),
                ),
            ),
            404: "Student not found",
        },
    )
    def get(self, request, student_id: int) -> Response:
        """
        Retrieve semester-wise results for a specific student.

        Args:
            request: The incoming HTTP request
            student_id: The unique identifier of the student

        Returns:
            JSON response containing student results grouped by semester
        """
        try:
            user = User.objects.get(id=student_id)
            student = Student.objects.get(user=user)
            results = StudentResult.objects.filter(student=student).select_related(
                "subject"
            )

            formatted_results = {}

            for result in results:
                semester = str(result.semester)
                if semester not in formatted_results:
                    formatted_results[semester] = {}

                subject_code = result.subject.code
                formatted_results[semester][subject_code] = {
                    "SUBJECT_CODE": subject_code,
                    "SUBJECT_NAME": result.subject.name.title(),
                    "CREDIT_HOUR": 3,
                    "GPA": result.gpa,
                }

            return Response(
                {
                    "message": "Teacher courses retrieved successfully",
                    "data": formatted_results,
                    "status": "data_retrieved",
                },
                status=status.HTTP_200_OK,
            )

        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND
            )
