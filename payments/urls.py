from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:course_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_cancel/', views.payment_cancel, name='payment_cancel'),
    path('my/', views.my_payments, name='my_payments'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
