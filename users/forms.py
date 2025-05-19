from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="",
        help_text="",
        widget=forms.TextInput(attrs={'placeholder': ''})
    )
    email = forms.EmailField(
        label="",
        help_text="",
        widget=forms.EmailInput(attrs={'placeholder': ''})
    )
    password1 = forms.CharField(
        label="",
        help_text="",
        widget=forms.PasswordInput(attrs={'placeholder': ''})
    )
    password2 = forms.CharField(
        label="",
        help_text="",
        widget=forms.PasswordInput(attrs={'placeholder': ''})
    )
    role = forms.ChoiceField(
        choices=(('student', 'Student'), ('teacher', 'Teacher')),
        label="",
        help_text=""
    )
    cv = forms.FileField(
        label="",
        help_text="",
        required=False
    )
    publications = forms.CharField(
        label="",
        help_text="",
        required=False,
        widget=forms.Textarea(attrs={'placeholder': '', 'rows': 3})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'cv', 'publications']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove all help texts
        for field in self.fields.values():
            field.help_text = ""

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Nom d’utilisateur ou e-mail')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username', 'email','profile_picture', 'cv', 'publications']

