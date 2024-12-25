from django.contrib import admin

from academics.models import Assignment, AssignmentSubmission, Course, Subject

# Register your models here.
admin.site.register(Subject)
admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
