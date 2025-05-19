from django.urls import path
from . import views

urlpatterns = [
        path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
        path('profile/', views.profile, name='profile'), 
            path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('delete/user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete/course/<int:course_id>/', views.delete_course, name='delete_course'),
]
