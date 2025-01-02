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
from EduTrack.permissions import CheckPermission, ModulePermission
from EduTrack.utils import get_or_not_found


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
            self.required_permission = [ModulePermission.ASSIGNMENT_VIEW]
        return super().get_permissions()

    def get_queryset(self, user):
        return Assignment.objects.filter(
            subject__semester=user.student_profile.semester
        ).select_related("subject", "created_by")

    @swagger_auto_schema(
        tags=["Assignments"],
        operation_summary="List student assignments",
        operation_description="""
            Retrieve all assignments for the student's current semester,
            including their submissions.
        """,
        responses={
            200: {
                "message": "Assignments retrieved successfully",
                "data": serializer_class(many=True),
                "status": "data_retrieved",
            },
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
    API endpoint for managing teacher assignments.
    Provides functionality for teachers to create new assignments and retrieve
    assignments they have created.
    """

    serializer_class = AssignmentSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = [ModulePermission.ASSIGNMENT_VIEW]
        else:
            self.required_permission = [ModulePermission.ASSIGNMENT_CREATE]
        return super().get_permissions()

    def get_queryset(self, user):
        return Assignment.objects.filter(
            created_by=user.teacher_profile
        ).select_related("subject", "created_by")

    @swagger_auto_schema(
        tags=["Assignments"],
        operation_summary="List teacher assignments",
        operation_description="Retrieve all assignments created by the authenticated teacher.",
        responses={
            200: {
                "message": "Teacher assignments retrieved successfully",
                "data": serializer_class(many=True),
                "status": "data_retrieved",
            }
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
                "message": "Teacher assignments retrieved successfully",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["Assignments"],
        operation_summary="Create assignment",
        operation_description="Create a new assignment for a specific subject.",
        request_body=AssignmentSerializer,
        responses={
            201: {
                "message": "Assignment created successfully",
                "data": serializer_class(many=True),
                "status": "created",
            }
        },
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
    API endpoint for managing individual assignments.
    Provides functionality to retrieve, update, and delete specific assignments.
    """

    serializer_class = AssignmentSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_permission = [ModulePermission.ASSIGNMENT_VIEW]
        elif self.request.method == "PATCH":
            self.required_permission = [ModulePermission.ASSIGNMENT_UPDATE]
        elif self.request.method == "DELETE":
            self.required_permission = [ModulePermission.ASSIGNMENT_DELETE]
        return super().get_permissions()

    def get_queryset(self, pk):
        return get_or_not_found(Assignment.objects.all(), pk=pk)

    @swagger_auto_schema(
        tags=["Assignments"],
        operation_summary="Get assignment details",
        operation_description="Retrieve details of a specific assignment.",
        responses={
            200: {
                "message": "Assignment details retrieved successfully",
                "data": serializer_class,
                "status": "data_retrieved",
            }
        },
    )
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
        tags=["Assignments"],
        operation_summary="Update assignment",
        operation_description="Update details of a specific assignment.",
        request_body=AssignmentSerializer,
        responses={
            200: {
                "message": "Assignment updated successfully",
                "data": serializer_class,
                "status": "updated",
            },
        },
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
        tags=["Assignments"],
        operation_summary="Delete assignment",
        operation_description="Delete a specific assignment.",
        responses={
            200: {"message": "Assignment deleted successfully", "status": "deleted"},
        },
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
    """
    API endpoint for managing student assignment submissions.
    Allows students to submit assignments and view their submissions.
    """

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
        tags=["Assignment Submissions"],
        operation_summary="List student submissions",
        operation_description="Retrieve all submissions made by the authenticated student.",
        responses={
            200: {
                "message": "Data retrieved successfully",
                "data": serializer_class,
                "status": "data_retrieved",
            }
        },
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
        tags=["Assignment Submissions"],
        operation_summary="Submit assignment",
        operation_description="Create a new submission for an assignment.",
        request_body=AssignmentSubmissionSerializer,
        responses={
            201: {
                "message": "Assignment Submission created successfully",
                "data": serializer_class,
                "status": "created",
            }
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
    """
    API endpoint for managing individual assignment submissions.
    Allows students to view and delete their submissions, and teachers to view
    all submissions for their assignments.
    """

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

    def get_queryset(self, pk):
        return get_or_not_found(AssignmentSubmission.objects.all(), pk=pk)

    @swagger_auto_schema(
        tags=["Assignment Submissions"],
        operation_summary="Delete submission",
        operation_description="Delete a specific assignment submission.",
        responses={
            200: {
                "message": "Assignment submission deleted successfully",
                "status": "deleted",
            }
        },
    )
    def delete(self, request, pk):
        submission = self.get_queryset(pk)

        submission.delete()
        return Response(
            {
                "message": "Assignment submission deleted successfully.",
                "status": "deleted",
            },
            status=status.HTTP_200_OK,
        )


class SubmissionByAssignmentView(APIView):
    """
    API endpoint for retrieving submissions by assignment.

    Allows teachers to view all submissions for a specific assignment.
    """

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
        tags=["Assignment Submissions"],
        operation_summary="List assignment submissions",
        operation_description="Retrieve all submissions for a specific assignment.",
        responses={
            200: {
                "message": "Submission retrieved successfully",
                "data": serializer_class(many=True),
                "status": "data_retrieved",
            }
        },
    )
    def get(self, request, pk):
        """Get list of assignment submission by assignment ID"""
        assignment = get_or_not_found(Assignment.objects.all(), pk=pk)
        assignment_submission = self.get_queryset(assignment)
        serializer = self.serializer_class(assignment_submission, many=True)
        return Response(
            {
                "message": "Submission retrieved successfully.",
                "data": serializer.data,
                "status": "data_retrieved",
            },
            status=status.HTTP_200_OK,
        )


class SubmissionGradeView(APIView):
    """
    API endpoint for grading assignment submissions.

    Allows teachers to grade and provide feedback on student submissions.
    """

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
        tags=["Assignment Submissions"],
        operation_summary="Grade submission",
        operation_description="Update grade and feedback for a submission.",
        request_body=AssignmentSubmissionSerializer,
        responses={
            200: {
                "message": "Assignment submission updated successfully",
                "data": serializer_class,
                "status": "updated",
            },
        },
    )
    def patch(self, request, pk):
        """Grade assignment submission by assignment submission ID"""
        submission = get_or_not_found(AssignmentSubmission.objects.all(), pk=pk)
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
            self.required_permission = [ModulePermission.COURSE_VIEW]
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
            200: {
                "message": "Course retrieved successfully",
                "data": serializer_class(many=True),
                "status": "data_retrieved",
            },
        },
    )
    def get(self, request):
        user = request.user
        courses = self.get_queryset(user)

        serializer = self.serializer_class(courses, many=True)
        return Response(
            {
                "message": "Course retrieved successfully",
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
    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = [ModulePermission.COURSE_VIEW]
        else:
            self.required_permission = [ModulePermission.COURSE_CREATE]
        return super().get_permissions()

    def get_queryset(self, user):
        return Course.objects.filter(teacher=user.teacher_profile).select_related(
            "subject", "teacher"
        )

    @swagger_auto_schema(
        tags=["Courses"],
        operation_summary="List teacher courses",
        operation_description="Retrieve all courses created by the teacher.",
        responses={
            200: {
                "message": "Teacher courses retrieved successfully",
                "data": serializer_class(many=True),
                "status": "data_retrieved",
            }
        },
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
        tags=["Courses"],
        operation_summary="Create course",
        operation_description="Create a new course.",
        request_body=CourseSerializer,
        responses={
            201: {
                "message": "Course created successfully",
                "data": serializer_class,
                "status": "created",
            }
        },
    )
    def post(self, request):
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
    API endpoint for managing individual courses.
    Provides functionality to retrieve, update, and delete specific courses.
    """

    serializer_class = CourseSerializer
    permission_classes = [CheckPermission]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_permission = [ModulePermission.COURSE_VIEW]
        elif self.request.method == "PATCH":
            self.required_permission = [ModulePermission.COURSE_UPDATE]
        elif self.request.method == "DELETE":
            self.required_permission = [ModulePermission.COURSE_DELETE]
        return super().get_permissions()

    def get_queryset(self, pk):
        return get_or_not_found(Course.objects.all(), pk=pk)

    @swagger_auto_schema(
        tags=["Courses"],
        operation_summary="Get course details",
        operation_description="Retrieve details of a specific course.",
        responses={
            200: {
                "message": "Course details retrieved successfully",
                "data": serializer_class,
                "status": "data_retrieved",
            },
        },
    )
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
        tags=["Courses"],
        operation_summary="Update course",
        operation_description="Update details of a specific course.",
        request_body=CourseSerializer,
        responses={
            200: {
                "message": "Course updated successfully",
                "data": serializer_class,
                "status": "updated",
            }
        },
    )
    def patch(self, request, pk):
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
        tags=["Courses"],
        operation_summary="Delete course",
        operation_description="Delete a specific course.",
        responses={
            200: {"message": "Course deleted successfully", "status": "deleted"}
        },
    )
    def delete(self, request, pk):
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
    API endpoint for managing course lessons.
    Allows teachers to create and manage lessons within their courses.
    """

    serializer_class = LessonSerializer

    permission_classes = [CheckPermission]

    def get_permissions(self):
        """
        Determines permissions based on the request method.
        """
        if self.request.method == "GET":
            self.required_permission = [ModulePermission.COURSE_VIEW]
        else:
            self.required_permission = [ModulePermission.COURSE_CREATE]
        return super().get_permissions()

    @swagger_auto_schema(
        tags=["Lessons"],
        operation_summary="Create lesson",
        operation_description="Create a new lesson for a course.",
        request_body=LessonSerializer,
        responses={
            201: {
                "message": "Lesson created successfully",
                "data": serializer_class,
                "status": "created",
            }
        },
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
