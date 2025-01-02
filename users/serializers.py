import re

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from EduTrack.utils import get_or_not_found
from users.models import Student, Teacher, User


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "profile_picture",
            "role_name",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = ["id", "user", "semester", "batch"]


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ["id", "user", "subjects"]

    def get_subjects(self, obj):
        teacher_subjects = obj.subject.all()
        return [
            {
                "id": sub.subject.id,
                "name": sub.subject.name,
                "code": sub.subject.code,
                "semester": sub.subject.semester,
            }
            for sub in teacher_subjects
        ]


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255, write_only=True, min_length=8)
    password2 = serializers.CharField(max_length=255, write_only=True, min_length=8)

    class Meta:
        fields = ["password", "password2"]

    def validate(self, obj):
        password = obj.get("password")
        password2 = obj.get("password2")
        uid = self.context.get("uid")
        token = self.context.get("token")

        try:
            user_id = smart_str(urlsafe_base64_decode(uid))
            self.user = get_or_not_found(User.objects.all(), pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {"message": ["Link is expired or invalid."]}
            )

        if not PasswordResetTokenGenerator().check_token(self.user, token):
            raise serializers.ValidationError(
                {"message": ["Link is expired or invalid."]}
            )

        self.validate_passwords(password, password2)

        return obj

    def create(self, validated_data):
        self.user.set_password(validated_data["password"])
        self.user.save()
        return self.user

    def validate_passwords(self, password, password2):
        if password != password2:
            raise serializers.ValidationError(
                {"message": ["Password and Confirm Password don't match"]}
            )
        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError(
                {"message": ["Password must contain at least one uppercase letter"]}
            )
        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError(
                {"message": ["Password must contain at least one lowercase letter"]}
            )
        if not re.search(r"\d", password):
            raise serializers.ValidationError(
                {"message": ["Password must contain at least one number"]}
            )
        if not re.search(r"[^\w\s]", password):
            raise serializers.ValidationError(
                {"message": ["Password must contain at least one special character"]}
            )
