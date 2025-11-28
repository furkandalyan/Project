from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/course/<int:course_id>/', views.student_course_detail, name='student_course_detail'),
    path('student/calendar/', views.student_calendar, name='student_calendar'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/announcements/new/', views.teacher_create_announcement, name='teacher_create_announcement'),
    path('teacher/calendar/', views.teacher_calendar, name='teacher_calendar'),
    path('teacher/calendar/ics/', views.teacher_calendar_ics, name='teacher_calendar_ics'),
    path('search/', views.global_search, name='global_search'),
    path('affairs/dashboard/', views.affairs_dashboard, name='affairs_dashboard'),

    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/course/<int:course_id>/', views.course_detail, name='course_detail'),

    path('teacher/course/<int:course_id>/add-lo/', views.add_lo, name='add_lo'),
    path('teacher/course/<int:course_id>/add-exam/', views.add_exam, name='add_exam'),
    path('teacher/exam/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('teacher/exam/<int:exam_id>/add-lo-weight/', views.add_exam_lo_weight, name='add_exam_lo_weight'),
    path('teacher/exam/<int:exam_id>/grades/', views.manage_exam_scores, name='manage_exam_scores'),
]
