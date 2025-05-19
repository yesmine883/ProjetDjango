from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/assignments/create/<str:type>/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('courses/<int:course_id>/assignments/create_file/', views.assignment_create_file, name='assignment_create_file'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('checkout/<int:course_id>/', views.checkout, name='checkout'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    path('assignment/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('courses/<int:course_id>/upload-assignment/', views.upload_assignment, name='upload_assignment'),
    path('<int:course_id>/students/', views.course_students_view, name='course_students'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/', views.dashboard, name='dashboardCourses'),
    path('all_course', views.all_course, name='all_course'),
     path('dashboarde/', views.dashboard_view, name='courses_dashboard'),
]
