from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Course)
# admin.site.register(AssignmentType)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Enrollment)