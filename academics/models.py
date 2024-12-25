from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models

from users.models import Student, Teacher


def assignment_submission_path(instance, filename):
    """
    Generate dynamic upload path for assignment submissions.
    Path will be: submissions/subject_id/assignment_id/student
    """
    if instance.assignment and instance.assignment.subject and instance.student:
        subject = instance.assignment.subject.name
        assignment = instance.assignment.id
        student = instance.student.id

        return f"submissions/{subject}/{assignment}/{student}/{filename}"

    return f"submissions/unknown/{filename}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    semester = models.IntegerField()

    def __str__(self):
        return f"{self.name}"


class TeacherSubject(models.Model):
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="subject"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="teacher"
    )


class Course(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    type = models.CharField(max_length=20)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def duration_formatted(self):
        duration = timedelta(minutes=self.duration_minutes)
        hours = duration.seconds // 3600
        minutes = (duration.seconds // 60) % 60
        if hours and minutes:
            return f"{hours} hr {minutes} min"
        elif hours:
            return f"{hours} hr"
        else:
            return f"{minutes} min"

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"({self.id}) {self.title}"


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, related_name="lesson_list", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField()
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["order"]
        unique_together = ["course", "order"]


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    due_date = models.DateTimeField()
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"({self.id}) {self.title}"


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_file = models.FileField(
        upload_to=assignment_submission_path, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(null=True, blank=True)

    def __str__(self):
        return (
            f"({self.id}) {self.student.user.get_full_name()} - {self.assignment.title}"
        )
