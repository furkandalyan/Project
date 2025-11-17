from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/course/<int:course_id>/', views.student_course_detail, name='student_course_detail'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('affairs/dashboard/', views.affairs_dashboard, name='affairs_dashboard'),

    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/course/<int:course_id>/', views.course_detail, name='course_detail'),

    path('teacher/course/<int:course_id>/add-lo/', views.add_lo, name='add_lo'),
    path('teacher/course/<int:course_id>/add-exam/', views.add_exam, name='add_exam'),
    path('teacher/exam/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('teacher/exam/<int:exam_id>/add-lo-weight/', views.add_exam_lo_weight, name='add_exam_lo_weight'),
]
