from bleach import ALLOWED_ATTRIBUTES, ALLOWED_TAGS, clean
from rest_framework import serializers

from academics.models import Assignment, AssignmentSubmission, Course, Lesson, Subject
from users.serializers import TeacherSerializer


class SubjectSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    code = serializers.CharField(max_length=10)
    semester = serializers.IntegerField()

    def create(self, validated_data):
        return Subject.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.code = validated_data.get("code", instance.code)
        instance.semester = validated_data.get("semester", instance.semester)
        instance.save()
        return instance


class LessonSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    title = serializers.CharField(max_length=200)
    content = serializers.CharField()
    order = serializers.IntegerField()
    duration_minutes = serializers.IntegerField(min_value=1)

    def validate_content(self, value):
        custom_tags = set(ALLOWED_TAGS) | {
            "h1",
            "h2",
            "h3",
            "p",
            "strong",
            "em",
            "u",
            "ol",
            "ul",
            "li",
            "blockquote",
        }

        custom_attributes = dict(ALLOWED_ATTRIBUTES)

        cleaned_content = clean(
            value, tags=custom_tags, attributes=custom_attributes, strip=True
        )

        return cleaned_content

    def create(self, validated_data):
        return Lesson.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.order = validated_data.get("order", instance.order)
        instance.duration_minutes = validated_data.get(
            "duration_minutes", instance.duration_minutes
        )
        instance.course = validated_data.get("course", instance.course)
        instance.save()
        return instance


class CourseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    type = serializers.CharField(max_length=20)
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, allow_blank=True)
    duration_minutes = serializers.IntegerField(min_value=1)
    duration = serializers.CharField(source="duration_formatted", read_only=True)
    teacher = TeacherSerializer(read_only=True)
    lesson_list = LessonSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def validate_duration_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be positive")
        return value

    def create(self, validated_data):
        teacher = self.context.get("teacher")
        return Course.objects.create(teacher=teacher, **validated_data)

    def update(self, instance, validated_data):
        instance.subject = validated_data.get("subject", instance.subject)
        instance.type = validated_data.get("type", instance.type)
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.duration_minutes = validated_data.get(
            "duration_minutes", instance.duration_minutes
        )
        instance.teacher = validated_data.get("teacher", instance.teacher)
        instance.save()
        return instance


class AssignmentSubmissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    assignment = serializers.PrimaryKeyRelatedField(queryset=Assignment.objects.all())
    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )
    submission_file = serializers.FileField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    score = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    feedback = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def create(self, validated_data):
        student = self.context.get("student")
        return AssignmentSubmission.objects.create(student=student, **validated_data)

    def update(self, instance, validated_data):
        instance.assignment = validated_data.get("assignment", instance.assignment)
        instance.student = validated_data.get("student", instance.student)
        instance.submission_file = validated_data.get(
            "submission_file", instance.submission_file
        )
        instance.score = validated_data.get("score", instance.score)
        instance.feedback = validated_data.get("feedback", instance.feedback)
        instance.save()
        return instance

    def validate_score(self, value):
        if value is not None:
            assignment = (
                self.instance.assignment
                if self.instance
                else self.initial_data.get("assignment")
            )
            if value > assignment.max_score:
                raise serializers.ValidationError(
                    f"Score cannot exceed the maximum score of {assignment.max_score}"
                )
        return value


class AssignmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    due_date = serializers.DateTimeField()
    max_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    created_by_name = serializers.CharField(
        source="created_by.first_name", read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    submission = serializers.SerializerMethodField()

    def get_submission(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if request.user.is_student():
            submissions = obj.submissions.filter(student=request.user.student_profile)
        else:
            submissions = obj.submissions.all()

        submission_data = AssignmentSubmissionSerializer(submissions, many=True).data

        return submission_data

    def validate_max_score(self, value):
        if value <= 0:
            raise serializers.ValidationError("Maximum score must be positive")
        return value

    def validate_due_date(self, value):
        from django.utils import timezone

        if value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value

    def create(self, validated_data):
        teacher = self.context.get("teacher")
        return Assignment.objects.create(created_by=teacher, **validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.subject = validated_data.get("subject", instance.subject)
        instance.due_date = validated_data.get("due_date", instance.due_date)
        instance.max_score = validated_data.get("max_score", instance.max_score)
        instance.created_by = validated_data.get("created_by", instance.created_by)
        instance.save()
        return instance
