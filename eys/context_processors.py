from django.urls import reverse
from django.utils import timezone

from .models import Exam, Notification

TEACHER_ROLES = {"Regular Instructor", "Advisor Instructor", "Head of Department"}


def navbar(request):
    """
    Navbar'da kullanılacak bildirim ve yaklaşan etkinlik sayıları.
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

    notifications = Notification.objects.filter(user=user).order_by("-created_at")[:5]
    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    activity_items = []
    for notif in notifications:
        ts = timezone.localtime(notif.created_at).strftime("%d.%m.%Y • %H:%M")
        activity_items.append(
            {
                "icon": "🔔",
                "title": notif.message,
                "subtitle": notif.kind,
                "timestamp": ts,
                "url": notif.url or "",
            }
        )

    if role_name == "Student":
        courses = user.courses_taken.all()
        upcoming_qs = Exam.objects.filter(course__in=courses, scheduled_at__gte=now)
        data["nav_upcoming_count"] = upcoming_qs.count()
    elif role_name in TEACHER_ROLES:
        courses = user.courses_given.all()
        upcoming_qs = Exam.objects.filter(course__in=courses, scheduled_at__gte=now)
        data["nav_upcoming_count"] = upcoming_qs.count()

    data["nav_notification_count"] = min(unread_count, 99)
    data["nav_upcoming_count"] = min(data["nav_upcoming_count"], 99)
    data["nav_activity_items"] = activity_items
    data["nav_notification_target"] = reverse("notifications")
    # Add dark mode preference
    data["dark_mode"] = user.dark_mode if hasattr(user, 'dark_mode') else False
    return data
