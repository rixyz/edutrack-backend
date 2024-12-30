from django.db import models

from academics.models import Subject
from users.models import Student


class StudentPerformanceMetrics(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    attendance_rate = models.FloatField()
    assignment_completion_rate = models.FloatField()
    average_assignment_score = models.FloatField()
    mid_term_grade = models.FloatField(null=True)

    def __str__(self):
        return f"{self.student} - {self.subject}"

    class Meta:
        unique_together = ("student", "subject")


class StudentResult(models.Model):
    """Stores final results for a student in a specific subject and semester"""

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.IntegerField()
    gpa = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ("student", "subject", "semester")
