from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Assignment, AssignmentSubmission, Course
from academics.serializers import (
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
    CourseSerializer,
    LessonSerializer,
)
from EduTrack.permissions import CheckPermission


class AssignmentStudentView(APIView):
    """
    API endpoint for students to retrieve assignments specific to their semester.
    Includes their own submissions.
    """

    serializer_class = AssignmentSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, user):
        return Assignment.objects.filter(
            subject__semester=user.student_profile.semester
        ).select_related("subject", "created_by")

    @swagger_auto_schema(
        tags=["Assignment"],
        operation_description="Retrieve courses for the student's current semester",
        operation_summary="Get student-specific courses",
        responses={
            200: CourseSerializer(many=True),
            401: "Unauthorized - Authentication required",
        },
    )
    def get(self, request):
        user = request.user
        assignments = self.get_queryset(user)

        serializer = self.serializer_class(
            assignments, many=True, context={"request": request}
        )
        return Response(
            {
                "message": "Assignments retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


class AssignmentTeacherView(APIView):
    """
    API view for teachers to retrieve their created assignments.
    """

    serializer_class = AssignmentSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, user):
        return Assignment.objects.filter(
            created_by=user.teacher_profile
        ).select_related("subject", "created_by")

    @swagger_auto_schema(
        tags=["Assignment"],
        operation_description="Get list of assignments created by the teacher",
        responses={200: AssignmentSerializer(many=True)},
    )
    def get(self, request):
        user = request.user
        assignments = self.get_queryset(user)
        serializer = self.serializer_class(
            assignments, many=True, context={"request": request}
        )
        return Response(
            {
                "message": "Teacher assignments retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Assignment"],
        operation_description="Create a new assignment",
        request_body=AssignmentSerializer,
        responses={201: AssignmentSerializer(), 400: "Bad Request", 403: "Forbidden"},
    )
    def post(self, request):
        """Create a new assignment"""

        teacher = request.user.teacher_profile
        serializer = self.serializer_class(
            data=request.data, context={"teacher": teacher}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Assignment created successfully.",
                "data": serializer.data,
                "status": "created",
            },
            status=status.HTTP_201_CREATED,
        )


class AssignmentDetailView(APIView):
    """
    API view for retrieving detailed information about a specific assignment.
    """

    serializer_class = AssignmentSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, pk):
        return Assignment.objects.get(pk=pk)

    def get(self, request, pk):
        """
        Retrieve details of a specific assignment.
        """
        assignments = self.get_queryset(pk)

        serializer = self.serializer_class(assignments, context={"request": request})
        return Response(
            {
                "message": "Assignment details retrieved successfully.",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Assignment"],
    )
    def patch(self, request, pk):
        """
        Update specific fields of an existing assignment.

        Args:
            request: HTTP request containing fields to update
            pk (int): Primary key of the assignment to update

        Returns:
            Response: Updated assignment data with HTTP 200 OK status or appropriate error response
        """
        assignment = self.get_queryset(pk)
        serializer = self.serializer_class(assignment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(
            {
                "message": "Assignment updated successfully.",
                "data": serializer.data,
                "status": "updated",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Assignment"],
    )
    def delete(self, request, pk):
        """
        Delete a specific assignment.

        Args:
            request: HTTP request
            pk (int): Primary key of the assignment to delete

        Returns:
            Response: Empty response with HTTP 204 NO CONTENT status or error response
        """
        assignment = self.get_queryset(pk)
        assignment.delete()
        return Response(
            {
                "message": "Assignment deleted successfully.",
                "status": "deleted",
            },
            status=status.HTTP_200_OK,
        )


class SubmissionStudentSubmitView(APIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, student):
        return AssignmentSubmission.objects.filter(student=student).select_related(
            "assignment", "student"
        )

    @swagger_auto_schema(
        tags=["Assignment Submission"],
        operation_description="Get list of assignment submissions",
        responses={200: AssignmentSubmissionSerializer(many=True)},
    )
    def get(self, request):
        """Get list of assignment submissions"""
        student = request.user.student_profile
        assignment_submission = self.get_queryset(student)
        serializer = self.serializer_class(assignment_submission, many=True)
        return Response(
            {
                "message": "Data retrieved successfully.",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Assignment Submission"],
        operation_description="Create a new assignment submission",
        request_body=AssignmentSubmissionSerializer,
        responses={
            201: AssignmentSubmissionSerializer(),
            400: "Bad Request",
            403: "Forbidden",
        },
    )
    def post(self, request):
        """Create a new assignment submission"""
        student = request.user.student_profile
        serializer = self.serializer_class(
            data=request.data, context={"student": student}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Assignment Submission created successfully.",
                "data": serializer.data,
                "status": "created",
            },
            status=status.HTTP_201_CREATED,
        )


class SubmissionDetailView(APIView):
    serializer_class = AssignmentSubmissionSerializer

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method in ["GET", "DELETE"]:
            self.permission_classes = []
        else:
            self.permission_classes = []
        return super().get_permissions()

    @swagger_auto_schema(
        tags=["Assignment Submission"],
        operation_description="Delete an assignment submission",
        responses={204: "No Content", 403: "Forbidden", 404: "Not Found"},
    )
    def delete(self, request, pk):
        """Delete an assignment submission"""
        student = request.user.student_profile
        submission = AssignmentSubmission.objects.get(pk=pk, student=student)

        submission.delete()
        return Response(
            {
                "message": "Assignment submission deleted successfully.",
                "status": "deleted",
            },
            status=status.HTTP_204_NO_CONTENT,
        )


class SubmissionByAssignmentView(APIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, assignment):
        return AssignmentSubmission.objects.filter(
            assignment=assignment
        ).select_related("assignment", "student")

    @swagger_auto_schema(
        tags=["Assignment Submission"],
        operation_description="Get list of assignment submission",
        responses={200: AssignmentSubmissionSerializer(many=True)},
    )
    def get(self, request, pk):
        """Get list of assignment submission by assignment ID"""
        assignment = Assignment.objects.get(pk=pk)
        assignment_submission = self.get_queryset(assignment)
        serializer = self.serializer_class(assignment_submission, many=True)
        return Response(
            {
                "message": "Data retrieved successfully.",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


class SubmissionGradeView(APIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    @swagger_auto_schema(
        tags=["Assignment Submission"],
        operation_description="Grade assignment submission",
        responses={200: AssignmentSubmissionSerializer(many=True)},
    )
    def patch(self, request, pk):
        """Grade assignment submission by assignment submission ID"""
        submission = AssignmentSubmission.objects.get(pk=pk)
        serializer = self.serializer_class(submission, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Assignment submission updated successfully.",
                "data": serializer.data,
                "status": "updated",
            },
            status=status.HTTP_200_OK,
        )


class CourseStudentView(APIView):
    """
    API endpoint for students to retrieve courses specific to their semester.

    Allows students to view courses relevant to their current academic semester.
    """

    serializer_class = CourseSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, user):
        return Course.objects.filter(
            subject__semester=user.student_profile.semester
        ).select_related("subject", "teacher")

    @swagger_auto_schema(
        tags=["Course"],
        operation_description="Retrieve courses for the student's current semester",
        operation_summary="Get student-specific courses",
        responses={
            200: CourseSerializer(many=True),
            401: "Unauthorized - Authentication required",
        },
    )
    def get(self, request):
        user = request.user
        courses = self.get_queryset(user)

        serializer = self.serializer_class(courses, many=True)
        return Response(
            {
                "message": "Data retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


class CourseTeacherView(APIView):
    """
    API view for teachers to retrieve their created courses.
    """

    serializer_class = CourseSerializer

    permission_classes = []

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, user):
        return Course.objects.filter(teacher=user.teacher_profile).select_related(
            "subject", "teacher"
        )

    @swagger_auto_schema(
        tags=["Course"],
        operation_description="Get list of courses created by the teacher",
        responses={200: CourseSerializer(many=True)},
    )
    def get(self, request):
        user = request.user
        courses = self.get_queryset(user)
        serializer = self.serializer_class(courses, many=True)
        return Response(
            {
                "message": "Teacher courses retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Course"],
        operation_description="Create a new course",
        request_body=CourseSerializer,
        responses={201: CourseSerializer(), 400: "Bad Request", 403: "Forbidden"},
    )
    def post(self, request):
        """Create a new course"""

        teacher = request.user.teacher_profile
        serializer = self.serializer_class(
            data=request.data, context={"teacher": teacher}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Course created successfully.",
                "data": serializer.data,
                "status": "created",
            },
            status=status.HTTP_201_CREATED,
        )


class CourseDetailView(APIView):
    """
    API view for retrieving detailed information about a specific course.
    """

    serializer_class = CourseSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_permission = []
        return super().get_permissions()

    def get_queryset(self, pk):
        return Course.objects.get(pk=pk)

    def get(self, request, pk):
        """
        Retrieve details of a specific course.
        """
        courses = self.get_queryset(pk)

        serializer = self.serializer_class(courses, context={"request": request})
        return Response(
            {
                "message": "Course details retrieved successfully.",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Course"],
    )
    def patch(self, request, pk):
        """
        Update specific fields of an existing course.

        Args:
            request: HTTP request containing fields to update
            pk (int): Primary key of the course to update

        Returns:
            Response: Updated course data with HTTP 200 OK status or appropriate error response
        """
        course = self.get_queryset(pk)
        serializer = self.serializer_class(course, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(
            {
                "message": "Course updated successfully.",
                "data": serializer.data,
                "status": "updated",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Course"],
    )
    def delete(self, request, pk):
        """
        Delete a specific course.

        Args:
            request: HTTP request
            pk (int): Primary key of the course to delete

        Returns:
            Response: Empty response with HTTP 204 NO CONTENT status or error response
        """
        course = self.get_queryset(pk)
        course.delete()
        return Response(
            {
                "message": "Course deleted successfully.",
                "status": "deleted",
            },
            status=status.HTTP_200_OK,
        )


class LessonTeacherView(APIView):
    """
    API view for teachers to retrieve their created lessons.
    """

    serializer_class = LessonSerializer

    permission_classes = []

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = []
        else:
            self.required_permission = []
        return super().get_permissions()

    @swagger_auto_schema(
        tags=["Lesson"],
        operation_description="Create a new course",
        request_body=CourseSerializer,
        responses={201: CourseSerializer(), 400: "Bad Request", 403: "Forbidden"},
    )
    def post(self, request):
        """Create a new course"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Lesson created successfully.",
                "data": serializer.data,
                "status": "created",
            },
            status=status.HTTP_201_CREATED,
        )