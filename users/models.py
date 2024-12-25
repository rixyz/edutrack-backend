# Create your models here.
import datetime
import os

from django import utils
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import models
from django.forms import ValidationError

from rbac.models import Role


def file_size(value):
    limit = 5 * 1024 * 1024
    if value.size > limit:
        raise ValidationError("File too large. Size should not exceed 5 MB.")


def rename_profile_picture(instance, filename):
    name, ext = os.path.splitext(filename)
    new_name = (
        instance.get_full_name().lower()
        + datetime.datetime.now().strftime("-%Y-%b-%d-%H-%M-%S")
        + ext
    )
    return "{}/{}".format("profile_picture", new_name)


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifiers."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        print("Created User")
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True ")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self.create_user(
            email, password, first_name="ADMIN", last_name=email, **extra_fields
        )


class User(AbstractUser):
    """Custom User model with email as primary identifier."""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, blank=True, null=True, related_name="role"
    )
    profile_picture = models.ImageField(
        upload_to=rename_profile_picture,
        default="profile_picture/default_profile.jpg",
        validators=[file_size],
    )
    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def is_teacher(self):
        """Check if user has a teacher role."""
        return self.role and self.role.name == "Teacher"

    def is_student(self):
        """Check if user has a student role."""
        return self.role and self.role.name == "Student"

    def get_password_reset_url(self):
        base64_encoded_id = utils.http.urlsafe_base64_encode(
            utils.encoding.force_bytes(self.id)
        )
        token = PasswordResetTokenGenerator().make_token(self)
        base_url = "http://localhost:5173"
        reset_url = f"{base_url}/forget_password/{base64_encoded_id}/{token}"
        return reset_url

    def __str__(self):
        return f"({self.id}) {self.email}"


class Student(models.Model):
    """Additional information for student users."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    semester = models.IntegerField()
    batch = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.get_full_name()}"


class Teacher(models.Model):
    """Additional information for teacher users."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="teacher_profile"
    )

    def __str__(self):
        return f"{self.user.get_full_name()}"
