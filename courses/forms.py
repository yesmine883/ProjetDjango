from django import forms
from .models import Course, Assignment, AssignmentSubmission

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'price']
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        exclude = ['course', 'type']


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['file']
