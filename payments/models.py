from django.db import models
from django.conf import settings
from courses.models import Course

class Payment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    stripe_payment_intent = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('succeeded', 'Succeeded'), ('failed', 'Failed'), ('pending', 'Pending')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email} - {self.course.title} - {self.status}"
