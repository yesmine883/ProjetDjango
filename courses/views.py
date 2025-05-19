from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

import stripe

from .models import Course, Assignment, AssignmentSubmission, Enrollment
from .forms import CourseForm, AssignmentForm, AssignmentSubmissionForm
from users.models import User

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def course_list(request):
    if request.user.is_student:
        # Exclude courses that the student is already enrolled in
        enrolled_courses = request.user.courses_enrolled.all()
        courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
    else:
        courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    assignments = Assignment.objects.filter(course=course).prefetch_related('submissions', 'submissions__student')
    is_enrolled = False

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
        if(is_enrolled):
            # redirect me to courses
            print("is enrolled")
            return render(request, 'courses/course_detail.html', {
                'course': course,
                'assignments': assignments,
                'is_enrolled': is_enrolled,
            })

        # Add student submissions to assignments for student view
        if request.user.is_student:
            for assignment in assignments:
                assignment.student_submission = assignment.submissions.filter(student=request.user).first()

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'assignments': assignments,
        'is_enrolled': is_enrolled,
    })






@login_required
def course_create(request):
    if request.user.role != 'teacher':
        messages.error(request, "Vous devez être enseignant pour créer un cours.")
        return redirect('course_list')

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, "Cours créé avec succès.")
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form})

@login_required
def course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce cours.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Cours modifié avec succès.")
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)

    return render(request, 'courses/course_form.html', {'form': form})

@login_required
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.teacher:
        messages.error(request, "Vous n'êtes pas autorisé à supprimer ce cours.")
        return redirect('course_detail', course_id=course_id)

    if request.method == 'POST':
        course.delete()
        messages.success(request, "Cours supprimé avec succès.")
        return redirect('dashboard')

    return redirect('course_detail', course_id=course_id)

@login_required
def assignment_create(request, course_id, type):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter un travail.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.type = type.upper()
            assignment.save()
            messages.success(request, f"{type.upper()} ajouté avec succès.")
            return redirect('course_detail', course_id=course.id)
    else:
        form = AssignmentForm(initial={'type': type.upper()})

    return render(request, 'courses/assignment_form.html', {
        'form': form,
        'course': course,
        'type': type.upper()
    })

def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    return render(request, 'courses/assignment_detail.html', {'assignment': assignment})

@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course

    # Check if student is enrolled in the course
    if not course.students.filter(id=request.user.id).exists():
        messages.error(request, "Vous devez être inscrit au cours pour soumettre un devoir.")
        return redirect('course_detail', course_id=course.id)

    # Check if student role
    if request.user.role != 'student':
        messages.error(request, "Seuls les étudiants peuvent soumettre un devoir.")
        return redirect('course_detail', course_id=course.id)

    # Check due date
    if assignment.due_date and assignment.due_date < timezone.now().date():
        messages.error(request, "La date limite de soumission est dépassée.")
        return redirect('course_detail', course_id=course.id)

    # Check for existing submission
    existing_submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    if request.method == 'POST':
        # Handle direct file upload from course detail page
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']

            # Validate file
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                messages.error(request, "Le fichier est trop volumineux. La taille maximale est de 10MB.")
                return redirect('course_detail', course_id=course.id)

            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.zip', '.rar', '.txt', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css']
            file_ext = uploaded_file.name.lower().split('.')[-1]
            if '.' + file_ext not in allowed_extensions:
                messages.error(request, f"Type de fichier non autorisé. Extensions autorisées: {', '.join(allowed_extensions)}")
                return redirect('course_detail', course_id=course.id)

            if existing_submission:
                # Update existing submission
                existing_submission.file = uploaded_file
                existing_submission.submitted_at = timezone.now()
                existing_submission.save()
                messages.success(request, "Votre soumission a été mise à jour avec succès.")
            else:
                # Create new submission
                submission = AssignmentSubmission(
                    assignment=assignment,
                    student=request.user,
                    file=uploaded_file
                )
                submission.save()
                messages.success(request, "Votre travail a été soumis avec succès.")

            return redirect('course_detail', course_id=course.id)
        else:
            # Handle form submission from assignment_submit.html
            form = AssignmentSubmissionForm(request.POST, request.FILES)
            if form.is_valid():
                if existing_submission:
                    # Update existing submission
                    existing_submission.file = form.cleaned_data['file']
                    existing_submission.submitted_at = timezone.now()
                    existing_submission.save()
                    messages.success(request, "Votre soumission a été mise à jour avec succès.")
                else:
                    # Create new submission
                    submission = form.save(commit=False)
                    submission.assignment = assignment
                    submission.student = request.user
                    submission.save()
                    messages.success(request, "Votre travail a été soumis avec succès.")
                return redirect('course_detail', course_id=course.id)
            else:
                messages.error(request, "Il y a eu une erreur lors de la soumission. Veuillez vérifier le fichier.")
    else:
        form = AssignmentSubmissionForm()

    return render(request, 'courses/assignment_submit.html', {
        'form': form,
        'assignment': assignment,
        'today': timezone.now().date(),
        'existing_submission': existing_submission,
    })

@login_required
@require_POST  # Only allow POST requests
def delete_assignment(request, assignment_id):
    try:
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        course = assignment.course

        # Check if the user is the teacher of this course
        if request.user != course.teacher:
            return JsonResponse({
                'success': False,
                'error': 'Vous n\'êtes pas autorisé à supprimer ce travail.'
            }, status=403)

        # Delete the file from storage if it exists
        if assignment.file:
            assignment.file.delete()

        # Delete the assignment
        assignment.delete()

        return JsonResponse({
            'success': True,
            'message': f'{assignment.get_type_display()} supprimé avec succès.'
        })
    except Assignment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Travail introuvable.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def assignment_create_file(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        messages.error(request, "Vous n'êtes pas autorisé à ajouter un travail.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        assignment_type = request.POST.get('assignment_type')
        uploaded_file = request.FILES.get('file')

        if assignment_type and uploaded_file:
            Assignment.objects.create(
                course=course,
                title=f"{assignment_type} - {uploaded_file.name}",
                description=f"Travail {assignment_type} ajouté via upload.",
                type=assignment_type.upper(),
                file=uploaded_file
            )
            messages.success(request, "Travail ajouté avec succès.")
        else:
            messages.error(request, "Erreur lors de l'ajout du travail.")

    return redirect('course_detail', course_id=course.id)

from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
        user = request.user
        enrolled_courses = Course.objects.filter(students=user)

        published_courses = None
        if hasattr(user, 'is_teacher') and user.is_teacher:
            published_courses = Course.objects.filter(teacher=user)

        return render(request, 'users/dashboard.html', {
            'enrolled_courses': enrolled_courses,
            'published_courses': published_courses,
            'user': user,
        })

@login_required
def dashboard_view(request):
    """Redirect to the main dashboard"""
    return redirect(reverse('dashboard'))


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if course.is_free():
        course.students.add(request.user)
        messages.success(request, "Inscription réussie au cours gratuit.")
        return redirect('course_detail', course_id=course.id)
    else:
        return redirect('checkout', course_id=course.id)

@login_required
def checkout(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    price_cents = int(course.price * 100)

    if request.method == "GET":
        return render(request, "courses/checkout.html", {
            "course": course,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        })

    if request.method == "POST":
        domain_url = request.build_absolute_uri('/')[:-1]
        request.session['course_id'] = course.id

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': course.title,
                        },
                        'unit_amount': price_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                metadata={
                    'course_id': course.id,
                    'user_id': request.user.id,
                },
                success_url=domain_url + '/payments/payment_success/',
                cancel_url=domain_url + '/payments/payment-cancel/',
            )
            return redirect(checkout_session.url)
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du paiement: {str(e)}")
            return redirect('course_detail', course_id=course.id)

    return redirect('course_detail', course_id=course.id)


@login_required
def upload_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == 'POST':
        assignment_type = request.POST.get('assignment_type')
        uploaded_file = request.FILES.get('file')

        if assignment_type and uploaded_file:
            Assignment.objects.create(
                course=course,
                type=assignment_type,  # <-- ici on utilise "type" et non "assignment_type"
                file=uploaded_file,
                title='Fichier téléchargé',  # Tu peux adapter le titre si besoin
                description=''  # Ou autre valeur par défaut
            )
            return redirect('course_detail', course_id=course_id)

    return redirect('course_detail', course_id=course_id)
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

@login_required
@user_passes_test(is_teacher)
def course_students_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    students = course.students.all()
    return render(request, 'courses/course_students.html', {
        'course': course,
        'students': students
    })

@login_required
def student_dashboard(request):
    enrolled_courses = request.user.courses.all()
    return render(request, "student_dashboard.html", {
        "enrolled_courses": enrolled_courses,
    })

def all_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    assignments = Assignment.objects.filter(course=course)
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(course=course, student=request.user).exists()
    return render(request, 'courses/all_course.html', {
        'course': course,
        'assignments': assignments,
        'is_enrolled': is_enrolled,
    })
