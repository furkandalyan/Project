from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/course/<int:course_id>/', views.student_course_detail, name='student_course_detail'),
    path('student/calendar/', views.student_calendar, name='student_calendar'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignment/<int:assignment_id>/', views.student_assignment_detail, name='student_assignment_detail'),
    path('student/materials/', views.student_materials, name='student_materials'),

    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/announcements/', views.teacher_announcements, name='teacher_announcements'),
    path('teacher/announcements/new/', views.teacher_create_announcement, name='teacher_create_announcement'),
    path('teacher/announcement/<int:ann_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('teacher/announcement/<int:ann_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('teacher/calendar/', views.teacher_calendar, name='teacher_calendar'),
    path('teacher/calendar/ics/', views.teacher_calendar_ics, name='teacher_calendar_ics'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/new/', views.teacher_assignment_create, name='teacher_assignment_create'),
    path('teacher/assignment/<int:assignment_id>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('teacher/assignment/<int:assignment_id>/criteria/', views.manage_assignment_criteria, name='manage_assignment_criteria'),
    path('teacher/assignment/<int:assignment_id>/groups/', views.manage_assignment_groups, name='manage_assignment_groups'),
    path('teacher/assignment/<int:assignment_id>/remind/', views.send_assignment_reminders, name='send_assignment_reminders'),
    path('teacher/assignment/<int:assignment_id>/export-csv/', views.export_submissions_csv, name='export_submissions_csv'),
    path('teacher/assignment/<int:assignment_id>/export-zip/', views.export_submissions_zip, name='export_submissions_zip'),
    path('teacher/exam/<int:exam_id>/remind/', views.send_exam_reminders, name='send_exam_reminders'),
    path('teacher/exam/<int:exam_id>/export-scores/', views.export_exam_scores_csv, name='export_exam_scores_csv'),
    path('teacher/materials/', views.teacher_materials, name='teacher_materials'),
    path('teacher/materials/new/', views.create_material, name='create_material'),

    path('announcement/<int:ann_id>/', views.announcement_detail, name='announcement_detail'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    path('search/', views.global_search, name='global_search'),
    path('affairs/dashboard/', views.affairs_dashboard, name='affairs_dashboard'),

    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('teacher/course/<int:course_id>/thresholds/', views.edit_course_threshold, name='edit_course_threshold'),

    path('teacher/course/<int:course_id>/add-lo/', views.add_lo, name='add_lo'),
    path('teacher/course/<int:course_id>/add-exam/', views.add_exam, name='add_exam'),
    path('teacher/exam/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('teacher/exam/<int:exam_id>/add-lo-weight/', views.add_exam_lo_weight, name='add_exam_lo_weight'),
    path('teacher/exam/<int:exam_id>/grades/', views.manage_exam_scores, name='manage_exam_scores'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
]
