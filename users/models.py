from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Étudiant'),
        ('teacher', 'Enseignant'),
        ('admin', 'admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)  # Pour les enseignants
    publications = models.TextField(blank=True, null=True)  # Pour les enseignants
    profile_picture = models.ImageField(upload_to='profile/', null=True, blank=True)  # Nouveau champ photo profil

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_admin(self):
        return self.role == 'admin'
