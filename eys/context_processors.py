from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .models import Announcement, Exam, LearningOutcome

TEACHER_ROLES = {"Regular Instructor", "Advisor Instructor", "Head of Department"}


def navbar(request):
    """
    Provides notification counts, recent activity items, and search placeholder for the navbar.
    """
    data = {
        "nav_notification_count": 0,
        "nav_notification_target": "/",
        "nav_upcoming_count": 0,
        "nav_search_placeholder": "Ders, sınav veya duyuru ara...",
        "nav_activity_items": [],
    }

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        data["nav_notification_target"] = reverse("login")
        return data

    role_name = user.role.name if getattr(user, "role", None) else None
    now = timezone.now()

    activity_items = []

    def append_activity(icon, title, subtitle, timestamp):
        activity_items.append(
            {
                "icon": icon,
                "title": title,
                "subtitle": subtitle,
                "timestamp": timestamp,
            }
        )

    if role_name == "Student":
        courses = user.courses_taken.all()
        ann_q = (
            Announcement.objects.filter(Q(course__in=courses) | Q(course__isnull=True))
            .order_by("-created_at")[:4]
        )
        upcoming_q = Exam.objects.filter(course__in=courses, scheduled_at__gte=now)
        exam_q = (
            Exam.objects.filter(course__in=courses)
            .order_by("-created_at")
            .select_related("course")[:3]
        )
        lo_q = (
            LearningOutcome.objects.filter(course__in=courses)
            .order_by("-created_at")
            .select_related("course")[:3]
        )

        for ann in ann_q:
            ts = timezone.localtime(ann.created_at).strftime("%d.%m.%Y · %H:%M")
            append_activity("📢", ann.title, ann.body[:70] or "Yeni duyuru", ts)
        for exam in exam_q:
            ts = timezone.localtime(exam.created_at).strftime("%d.%m.%Y · %H:%M")
            append_activity("📝", f"{exam.course.code} • {exam.name}", "Yeni sınav oluşturuldu", ts)
        for lo in lo_q:
            ts = lo.created_at and timezone.localtime(lo.created_at).strftime("%d.%m.%Y · %H:%M") or ""
            append_activity("🎯", f"{lo.course.code} • Yeni LO", lo.title, ts)

        data["nav_notification_count"] = len(activity_items)
        data["nav_upcoming_count"] = upcoming_q.count()
        data["nav_notification_target"] = reverse("student_announcements")
    elif role_name in TEACHER_ROLES:
        courses = user.courses_given.all()
        ann_q = (
            Announcement.objects.filter(Q(author=user) | Q(course__in=courses))
            .order_by("-created_at")[:4]
        )
        upcoming_q = Exam.objects.filter(course__in=courses, scheduled_at__gte=now)
        exam_q = (
            Exam.objects.filter(course__in=courses)
            .order_by("-created_at")
            .select_related("course")[:3]
        )
        lo_q = (
            LearningOutcome.objects.filter(course__in=courses)
            .order_by("-created_at")
            .select_related("course")[:3]
        )

        for ann in ann_q:
            ts = timezone.localtime(ann.created_at).strftime("%d.%m.%Y · %H:%M")
            append_activity("📢", ann.title, ann.body[:70] or "Yeni duyuru", ts)
        for exam in exam_q:
            ts = timezone.localtime(exam.created_at).strftime("%d.%m.%Y · %H:%M")
            append_activity("📝", f"{exam.course.code} • {exam.name}", "Yeni sınav kaydı", ts)
        for lo in lo_q:
            ts = lo.created_at and timezone.localtime(lo.created_at).strftime("%d.%m.%Y · %H:%M") or ""
            append_activity("🎯", f"{lo.course.code} • Yeni LO", lo.title, ts)

        data["nav_notification_count"] = len(activity_items)
        data["nav_upcoming_count"] = upcoming_q.count()
        data["nav_notification_target"] = reverse("teacher_create_announcement")
    else:
        data["nav_notification_target"] = reverse("home")

    data["nav_notification_count"] = min(data["nav_notification_count"], 99)
    data["nav_upcoming_count"] = min(data["nav_upcoming_count"], 99)
    data["nav_activity_items"] = activity_items[:5]
    return data
