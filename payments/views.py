from django.contrib import messages
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import Payment
from courses.models import Course, Enrollment
from users.models import User

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',  # Changed to EUR to match the rest of the application
                    'unit_amount': int(course.price * 100),  # Convert to cents
                    'product_data': {
                        'name': course.title,
                    },
                },
                'quantity': 1,
            }],
            metadata={
                'course_id': course.id,
                'user_id': request.user.id,
            },
            mode='payment',
            success_url=request.build_absolute_uri('/payments/payment_success/'),
            cancel_url=request.build_absolute_uri('/payments/payment-cancel/'),
        )
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Erreur lors de la création du paiement: {str(e)}")
        return redirect('course_detail', course_id=course_id)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            course_id = session['metadata']['course_id']
            user_id = session['metadata']['user_id']

            # Create payment record
            Payment.objects.create(
                student_id=user_id,
                course_id=course_id,
                stripe_payment_intent=session['payment_intent'],
                amount=session['amount_total'] / 100,
                status='succeeded'
            )

            # Add student to course
            try:
                course = Course.objects.get(id=course_id)
                user = User.objects.get(id=user_id)
                course.students.add(user)
                
                # Create enrollment record
                Enrollment.objects.get_or_create(
                    student=user,
                    course=course,
                )
            except (Course.DoesNotExist, User.DoesNotExist):
                return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(status=400)

    return HttpResponse(status=200)

@login_required
def payment_success(request):
    course_id = request.session.get('course_id')
    
    if not course_id:
        messages.error(request, "Aucun cours trouvé pour cette transaction.")
        return redirect('course_list')

    try:
        course = Course.objects.get(id=course_id)
        
        # Add the student to the course
        course.students.add(request.user)
        
        # Create enrollment record
        Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
        )
        
        # Create payment record
        Payment.objects.create(
            student=request.user,
            course=course,
            amount=course.price,
            status='succeeded',
            stripe_payment_intent='manual_success'  # Since we don't have the actual payment intent here
        )
        
        messages.success(request, f"Félicitations ! Vous êtes maintenant inscrit au cours : {course.title}")
        
        # Clean up the session
        if 'course_id' in request.session:
            del request.session['course_id']
        
        return render(request, "payments/payment_success.html", {
            "course": course,
            "show_dashboard_link": True
        })
        
    except Course.DoesNotExist:
        messages.error(request, "Le cours demandé n'existe pas.")
        return redirect('course_list')
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de l'inscription : {str(e)}")
        return redirect('course_list')

@login_required
def payment_cancel(request):
    return render(request, 'payments/payment_cancel.html')

@login_required
def my_payments(request):
    payments = Payment.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'payments/my_payments.html', {'payments': payments})
