from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseForbidden

from courses.models import Course, Assignment, AssignmentSubmission, Enrollment
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileForm
from .models import User
from payments.models import Payment

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                              password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required

def dashboard(request):
    context = {}
    user = request.user
    print("test")
    print(f"DEBUG: User role: {user.role}")
    print(f"DEBUG: Is admin method: {user.is_admin()}")
    
    # Add debug information
    context.update({
        'debug_role': user.role,
        'debug_is_admin': user.is_admin(),
    })

    if user.role == 'admin':  # Check admin first
        print("DEBUG: Entering admin section")
        try:
            # Teacher statistics
            teachers = User.objects.filter(role='teacher')
            print(f"DEBUG: Found {teachers.count()} teachers")
            
            for teacher in teachers:
                teacher.course_count = Course.objects.filter(teacher=teacher).count()
                teacher.student_count = Course.objects.filter(teacher=teacher).aggregate(
                    total_students=Count('students', distinct=True))['total_students'] or 0

            # Student statistics
            students = User.objects.filter(role='student')
            print(f"DEBUG: Found {students.count()} students")
            
            for student in students:
                student.enrolled_courses_count = student.courses_enrolled.count()
                student.total_payments = Payment.objects.filter(student=student).aggregate(
                    total=Sum('amount'))['total'] or 0

            # Payment statistics
            all_payments = Payment.objects.all().order_by('-created_at')
            total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
            recent_payments = Payment.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).order_by('-created_at')
            print(f"DEBUG: Found {all_payments.count()} payments, total revenue: {total_revenue}")

            # Course statistics
            courses = Course.objects.all()
            print(f"DEBUG: Found {courses.count()} courses")
            
            for course in courses:
                course.enrollment_count = course.students.count()
                course.revenue = Payment.objects.filter(course=course).aggregate(
                    total=Sum('amount'))['total'] or 0

            context.update({
                'teachers': teachers,
                'students': students,
                'all_payments': all_payments,
                'total_revenue': total_revenue,
                'recent_payments': recent_payments,
                'courses': courses,
                'total_teachers': teachers.count(),
                'total_students': students.count(),
                'total_courses': courses.count(),
            })
            print("DEBUG: Successfully updated context with admin data")
        except Exception as e:
            print(f"DEBUG: Error in admin section: {str(e)}")
            messages.error(request, f"Erreur lors du chargement des données: {str(e)}")

    elif user.is_teacher:
        print("DEBUG: Entering teacher section")
        published_courses = user.courses_taught.all()
        context['published_courses'] = published_courses
        # Add teacher's course statistics
        for course in published_courses:
            course.student_count = course.students.count()
            course.submission_count = AssignmentSubmission.objects.filter(assignment__course=course).count()

    elif user.is_student:
        print("DEBUG: Entering student section")
        enrolled_courses = user.courses_enrolled.all()
        context['enrolled_courses'] = enrolled_courses
        # Add student's payment history
        context['payments'] = Payment.objects.filter(student=user).order_by('-created_at')

    return render(request, 'users/dashboard.html', context)

@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})

def index(request):
    return render(request, 'users/index.html')

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('profile')
        else:
            messages.error(request, 'Il y a eu une erreur lors de la mise à jour de votre profil.')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'users/edit_profile.html', {'form': form})

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user_to_delete = User.objects.get(id=user_id)
            if user_to_delete != request.user:  # Prevent admin from deleting themselves
                username = user_to_delete.username
                user_to_delete.delete()
                messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
            else:
                messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        except User.DoesNotExist:
            messages.error(request, "Utilisateur non trouvé.")
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
def delete_course(request, course_id):
    if request.method == 'POST':
        try:
            course = Course.objects.get(id=course_id)
            title = course.title
            course.delete()
            messages.success(request, f"Le cours '{title}' a été supprimé avec succès.")
        except Course.DoesNotExist:
            messages.error(request, "Cours non trouvé.")
    return redirect('dashboard')
