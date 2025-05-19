from django.conf import settings
from django.db import models
from users.models import User  # Assure-toi que User a bien l'attribut "role" (student, teacher, admin)


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught'
    )
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='courses_enrolled',
        blank=True
    )

    def __str__(self):
        return self.title

    def is_free(self):
        return self.price == 0.00


class AssignmentType(models.TextChoices):
    _meta = 'meta', 'Meta'
    TD = 'TD', 'Travaux Dirigés'
    TP = 'TP', 'Travaux Pratiques'


class Assignment(models.Model):
    course = models.ForeignKey(
        Course,
        related_name='assignments',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(
        max_length=50,
        choices=AssignmentType.choices
    )
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

    def get_student_submission(self, student):
        """Get the submission for a specific student"""
        return self.submissions.filter(student=student).first()


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'}
    )
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.username} - {self.assignment.title}'


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)
