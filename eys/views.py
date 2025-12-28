from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
import csv
import io
import zipfile

from django.db.models import Avg, Count, Q, Max, Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from requests import delete

User = get_user_model()

from .models import (
    Course,
    CourseThreshold,
    LearningOutcome,
    Exam,
    ExamLOWeight,
    Announcement,
    ExamResult,
    AnnouncementComment,
    Assignment,
    Submission,
    Notification,
    SubmissionAttachment,
    AssignmentCriterion,
    SubmissionCriterionScore,
    AssignmentGroup,
    CourseMaterial,
    AssignmentTemplate,
)
from .forms import (
    LOForm,
    ExamForm,
    ExamLOWeightForm,
    AnnouncementForm,
    ProfileUpdateForm,
    CommentForm,
    AssignmentForm,
    SubmissionForm,
    GradeSubmissionForm,
    PasswordChangeForm,
    ProfilePictureForm,
    AssignmentCriterionForm,
    AssignmentGroupForm,
    CourseMaterialForm,
    AssignmentTemplateForm,
    CourseThresholdForm,
)

DAY_LABELS = [
    "Pazartesi",
    "Salı",
    "Çarşamba",
    "Perşembe",
    "Cuma",
    "Cumartesi",
    "Pazar",
]

MONTH_LABELS = [
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
]

TEACHER_ROLES = {"Regular Instructor", "Advisor Instructor", "Head of Department"}


def create_notification(user, kind, message, url="", payload=""):
    if not user:
        return
    Notification.objects.create(
        user=user,
        kind=kind,
        message=message[:255],
        url=url or "",
        payload=payload or "",
    )


def get_course_threshold(course):
    threshold, _ = CourseThreshold.objects.get_or_create(
        course=course,
        defaults={
            "stable_min": 80,
            "watch_min": 65,
            "pass_min": 60,
        },
    )
    return threshold


def serialize_exam_for_student(exam, now=None):
    now = now or timezone.now()
    scheduled_local = timezone.localtime(exam.scheduled_at) if exam.scheduled_at else None
    upcoming_window = now + timedelta(days=3)
    end_of_week = timezone.localtime(now).date()
    end_of_week = end_of_week + timedelta(days=(6 - end_of_week.weekday()))
    palette = [
        "#1db954",
        "#2459c3",
        "#b86a00",
        "#ff6b6b",
        "#7d5fff",
        "#00a8e8",
        "#e91e63",
        "#2ecc71",
        "#9c27b0",
    ]
    code_sum = sum(ord(ch) for ch in (exam.course.code or str(exam.course_id)))
    course_color = palette[code_sum % len(palette)]

    return {
        "id": exam.id,
        "name": exam.name,
        "course_id": exam.course_id,
        "course_name": exam.course.name,
        "course_code": exam.course.code,
        "description": exam.description or "",
        "scheduled_local": scheduled_local,
        "scheduled_date": scheduled_local.strftime("%d.%m.%Y") if scheduled_local else None,
        "time_label": scheduled_local.strftime("%H:%M") if scheduled_local else None,
        "display_label": scheduled_local.strftime("%d.%m.%Y · %H:%M") if scheduled_local else "Tarih bekleniyor",
        "status": (
            "past"
            if scheduled_local and scheduled_local < now
            else (
                "soon"
                if scheduled_local and now <= scheduled_local <= upcoming_window
                else (
                    "this_week"
                    if scheduled_local and scheduled_local.date() <= end_of_week
                    else "future"
                )
            )
        ),
        "has_schedule": scheduled_local is not None,
        "day": scheduled_local.day if scheduled_local else None,
        "month": scheduled_local.month if scheduled_local else None,
        "year": scheduled_local.year if scheduled_local else None,
        "weekday_index": scheduled_local.weekday() if scheduled_local else None,
        "score": getattr(exam, "score", None),
        "course_color": course_color,
        "type_label": (
            "Vize" if (exam.name or "").lower().find("vize") != -1 or (exam.name or "").lower().find("midterm") != -1
            else ("Final" if (exam.name or "").lower().find("final") != -1
            else ("Quiz" if (exam.name or "").lower().find("quiz") != -1 or (exam.name or "").lower().find("kısa") != -1
            else None))
        ),
    }

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Role Check
            if not user.role:
                 messages.error(request, "Bu kullanıcının yetki rolü atanmamış.")
                 return render(request, "eys/login.html", {"hide_navbar": True})
                 
            role_name = user.role.name
            if role_name == "Student":
                return redirect("student_dashboard")
            elif role_name in ["Regular Instructor", "Advisor Instructor", "Head of Department"]:
                return redirect("teacher_dashboard")
            elif role_name == "Student Affairs":
                return redirect("affairs_dashboard")
            else:
                messages.error(request, f"Bilinmeyen rol: {role_name}. Lütfen yöneticiyle iletişime geçin.")
                # Yine de login kalsın mı? Güvenlik gereği logout yapılabilir.
                # logout(request)
        else:
            messages.error(request, "Kullanıcı adı veya parola hatalı.")
            
    return render(request, "eys/login.html", {"hide_navbar": True})

def user_logout(request):
    logout(request)
    return redirect("login")


def change_password(request):
    """Password change for unauthenticated users"""
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            old_password = form.cleaned_data.get("old_password")
            new_password = form.cleaned_data.get("new_password")
            
            # Authenticate user with old password
            user = authenticate(request, username=username, password=old_password)
            if user is not None:
                # Set new password
                user.set_password(new_password)
                user.save()
                messages.success(request, "Parolanız başarıyla değiştirildi. Yeni parolanızla giriş yapabilirsiniz.")
                return redirect("login")
            else:
                messages.error(request, "Kullanıcı adı veya mevcut parola hatalı.")
    else:
        form = PasswordChangeForm()
    
    return render(request, "eys/change_password.html", {"hide_navbar": True, "form": form})


@login_required
def upload_profile_picture(request):
    """Upload or update user profile picture"""
    if request.method == "POST":
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Validate file size (max 5MB)
            profile_picture = form.cleaned_data.get('profile_picture')
            if profile_picture:
                if profile_picture.size > 5 * 1024 * 1024:  # 5MB
                    messages.error(request, "Dosya boyutu 5MB'dan büyük olamaz.")
                else:
                    form.save()
                    messages.success(request, "Profil fotoğrafınız başarıyla güncellendi.")
        else:
            messages.error(request, "Profil fotoğrafı yüklenirken bir hata oluştu.")
    
    # Redirect back to the previous page or home
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def settings_view(request):
    """Settings page for user preferences"""
    if request.method == "POST":
        dark_mode = request.POST.get('dark_mode') == 'on'
        request.user.dark_mode = dark_mode
        request.user.save()
        messages.success(request, "Ayarlar başarıyla kaydedildi.")
        return redirect('settings')
    
    context = {
        'dark_mode': request.user.dark_mode if request.user.is_authenticated else False,
    }
    return render(request, "eys/settings.html", context)

def home(request):
    return render(request, "eys/home.html")

def student_dashboard(request):
    courses = (
        request.user.courses_taken.all().prefetch_related("learningoutcome_set", "exam_set")
    )
    lo_qs = LearningOutcome.objects.filter(course__in=courses).prefetch_related("examloweight_set__exam")
    exams_qs = Exam.objects.filter(course__in=courses).select_related("course")

    now = timezone.now()

    result_map = {
        res.exam_id: res.score
        for res in ExamResult.objects.filter(student=request.user, exam__in=exams_qs)
    }

    sample_los = list(lo_qs[:4])
    lo_success_data = []

    for lo in sample_los:
        total = Decimal("0")
        total_weight = Decimal("0")
        for weight in lo.examloweight_set.all():
            weight_percent = Decimal(str(weight.weight or 0))
            total_weight += weight_percent
            score = result_map.get(weight.exam_id)
            if score is not None:
                total += Decimal(score) * (weight_percent / Decimal("100"))
        if total_weight > 0 and total > 0:
            lo_success_data.append(
                {
                    "label": lo.title or f"LO {lo.id}",
                    "percent": round(min(Decimal("100"), total), 2),
                }
            )

    if not lo_success_data:
        lo_success_data = [
            {"label": "LO 1", "percent": 80},
            {"label": "LO 2", "percent": 65},
            {"label": "LO 3", "percent": 92},
        ]

    results_map = {
        res.exam_id: res.score
        for res in ExamResult.objects.filter(student=request.user, exam__in=exams_qs)
    }

    exam_results = []
    for exam in exams_qs.order_by("-scheduled_at")[:5]:
        exam.score = results_map.get(exam.id)
        exam_results.append(serialize_exam_for_student(exam, now))

    upcoming_exams = [
        serialize_exam_for_student(exam, now)
        for exam in exams_qs.filter(scheduled_at__isnull=False, scheduled_at__gte=now)
        .order_by("scheduled_at")[:5]
    ]

    calendar_buckets = defaultdict(list)
    for exam in exams_qs.filter(scheduled_at__isnull=False).order_by("scheduled_at"):
        data = serialize_exam_for_student(exam, now)
        if data["scheduled_local"]:
            calendar_buckets[data["scheduled_local"].date()].append(data)

    calendar_days = []
    for day in sorted(calendar_buckets.keys()):
        month_label = MONTH_LABELS[day.month - 1]
        day_label = DAY_LABELS[day.weekday()]
        calendar_days.append(
            {
                "date_label": f"{day.day} {month_label} {day.year}",
                "day_label": day_label,
                "items": calendar_buckets[day],
            }
        )
    calendar_days = calendar_days[:4]

    announcement_qs = (
        Announcement.objects.filter(
            Q(course__in=courses) | Q(course__isnull=True)
        )
        .select_related("course", "author")
        .order_by("-pinned", "-created_at")[:3]
    )

    announcement_cards = []
    for ann in announcement_qs:
        local_created = timezone.localtime(ann.created_at)
        month_label = MONTH_LABELS[local_created.month - 1]
        created_label = f"{local_created.day} {month_label} {local_created.year} · {local_created.strftime('%H:%M')}"
        author_name = (
            ann.author.get_full_name()
            if ann.author and ann.author.get_full_name()
            else getattr(ann.author, "username", "Sistem")
        )
        announcement_cards.append(
            {
                "id": ann.id,
                "title": ann.title,
                "body": ann.body,
                "attachment": ann.attachment,
                "meta": f"{author_name} • {created_label}",
                "course_label": f"{ann.course.code} · {ann.course.name}"
                if ann.course
                else "Genel Duyuru",
            }
        )
    if not announcement_cards:
        announcement_cards = [
            {
                "id": None,
                "title": "Henüz duyuru yok",
                "meta": "Takipte kal",
                "body": "Öğretim elemanlarınız duyuru paylaştığında burada göreceksin.",
                "course_label": "",
                "attachment": None,
            }
        ]

    return render(
        request,
        "eys/student_dashboard.html",
        {
            "course_count": courses.count(),
            "lo_total": lo_qs.count(),
            "exam_total": exams_qs.count(),
            "lo_success_data": lo_success_data,
            "exam_results": exam_results,
            "upcoming_exams": upcoming_exams,
            "calendar_days": calendar_days,
            "announcement_cards": announcement_cards,
        },
    )

def student_courses(request):
    courses_qs = (
        request.user.courses_taken.all()
        .select_related("instructor")
        .prefetch_related("learningoutcome_set", "exam_set", "students")
    )
    courses = list(courses_qs)
    now = timezone.now()

    for course in courses:
        serialized_next = None
        exam_list = sorted(
            [exam for exam in course.exam_set.all() if exam.scheduled_at],
            key=lambda exam: exam.scheduled_at,
        )
        if exam_list:
            upcoming = [exam for exam in exam_list if exam.scheduled_at >= now]
            next_exam = upcoming[0] if upcoming else exam_list[0]
            serialized_next = serialize_exam_for_student(next_exam, now)
        course.next_exam_card = serialized_next
        course.student_total = course.students.count()

    return render(request, "eys/student_courses.html", {"courses": courses})


def student_course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, students=request.user
    )
    los = LearningOutcome.objects.filter(course=course).prefetch_related("examloweight_set__exam")
    exams = (
        Exam.objects.filter(course=course)
        .select_related("course")
        .prefetch_related("examloweight_set__learning_outcome")
        .order_by("scheduled_at", "id")
    )
    now = timezone.now()
    student_result_map = {
        res.exam_id: res.score
        for res in ExamResult.objects.filter(student=request.user, exam__in=exams)
    }
    exam_cards = []
    for exam in exams:
        exam.score = student_result_map.get(exam.id)
        exam_cards.append(serialize_exam_for_student(exam, now))
    for lo in los:
        total = Decimal("0")
        total_weight = Decimal("0")
        for weight in lo.examloweight_set.all():
            weight_percent = Decimal(str(weight.weight or 0))
            total_weight += weight_percent
            score = student_result_map.get(weight.exam_id)
            if score is not None:
                total += Decimal(score) * (weight_percent / Decimal("100"))
        if total_weight > 0 and total > 0:
            lo.student_score = round(min(Decimal("100"), total), 2)
        else:
            lo.student_score = None
        lo.score_coverage = total_weight

    context = {
        "course": course,
        "los": los,
        "exams": exams,
        "exam_cards": exam_cards,
        "student_count": course.students.count(),
        "term_label": getattr(course, "term", None) or "Belirtilmedi",
        "instructor_name": course.instructor.get_full_name()
        if course.instructor and course.instructor.get_full_name()
        else getattr(course.instructor, "username", "Atanmadı"),
    }
    return render(request, "eys/student_course_detail.html", context)


def student_announcements(request):
    courses = request.user.courses_taken.all()
    show_pinned_only = request.GET.get("pinned") == "1"
    base_qs = Announcement.objects.filter(Q(course__in=courses) | Q(course__isnull=True))
    if show_pinned_only:
        base_qs = base_qs.filter(pinned=True)
    announcement_qs = (
        base_qs.select_related("course", "author").order_by("-pinned", "-created_at")
    )

    grouped = defaultdict(list)
    for ann in announcement_qs:
        local_created = timezone.localtime(ann.created_at)
        date_key = local_created.date()
        month_label = MONTH_LABELS[local_created.month - 1]
        timestamp = f"{local_created.day} {month_label} {local_created.year} · {local_created.strftime('%H:%M')}"
        author_name = (
            ann.author.get_full_name()
            if ann.author and ann.author.get_full_name()
            else getattr(ann.author, "username", "Sistem")
        )
        grouped[date_key].append(
            {
                "id": ann.id,
                "title": ann.title,
                "body": ann.body,
                "attachment": ann.attachment,
                "course_label": f"{ann.course.code} · {ann.course.name}" if ann.course else "Genel Duyuru",
                "timestamp": timestamp,
                "author_name": author_name,
                "author_initials": author_name[:2].upper(),
            }
        )

    timeline = []
    for day in sorted(grouped.keys(), reverse=True):
        month_label = MONTH_LABELS[day.month - 1]
        timeline.append(
            {
                "date_label": f"{day.day} {month_label} {day.year}",
                "items": grouped[day],
            }
        )

    return render(
        request,
        "eys/student_announcements.html",
        {
            "timeline": timeline,
            "total_count": announcement_qs.count(),
            "show_pinned_only": show_pinned_only,
        },
    )


def student_profile(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.role or request.user.role.name != "Student":
        messages.error(request, "Bu alan yalnızca öğrenciler içindir.")
        return redirect("home")

    initial_data = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
    }

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            new_password = form.cleaned_data.get("new_password")
            if new_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
            messages.success(request, "Profil bilgilerin güncellendi.")
            return redirect("student_profile")
    else:
        form = ProfileUpdateForm(initial=initial_data, instance=request.user)

    last_login = (
        timezone.localtime(request.user.last_login).strftime("%d.%m.%Y · %H:%M")
        if request.user.last_login
        else "Henüz giriş yapılmadı"
    )
    joined_date = timezone.localtime(request.user.date_joined).strftime("%d.%m.%Y")
    role_name = request.user.role.name if request.user.role else "Tanımsız"

    context = {
        "form": form,
        "last_login": last_login,
        "joined_date": joined_date,
        "role_name": role_name,
        "username": request.user.username,
    }
    return render(request, "eys/student_profile.html", context)


def student_calendar(request):
    now = timezone.localtime(timezone.now())
    today = timezone.localdate()

    try:
        selected_month = int(request.GET.get("month", now.month))
        selected_year = int(request.GET.get("year", now.year))
    except ValueError:
        selected_month = now.month
        selected_year = now.year

    if selected_month < 1 or selected_month > 12:
        selected_month = now.month
    if selected_year < 1900 or selected_year > 2100:
        selected_year = now.year

    def shift_month(year, month, delta):
        month += delta
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        return year, month

    prev_year, prev_month = shift_month(selected_year, selected_month, -1)
    next_year, next_month = shift_month(selected_year, selected_month, 1)

    courses = request.user.courses_taken.all()
    exams_qs = (
        Exam.objects.filter(course__in=courses, scheduled_at__isnull=False)
        .select_related("course")
        .order_by("scheduled_at")
    )
    serialized_exams = [serialize_exam_for_student(exam, now) for exam in exams_qs]

    exams_by_date = defaultdict(list)
    for exam in serialized_exams:
        if exam["scheduled_local"]:
            exams_by_date[exam["scheduled_local"].date()].append(exam)

    days_in_month = monthrange(selected_year, selected_month)[1]
    first_weekday = date(selected_year, selected_month, 1).weekday()  # Monday = 0

    month_cells = []
    for _ in range(first_weekday):
        month_cells.append(None)

    for day in range(1, days_in_month + 1):
        current_date = date(selected_year, selected_month, day)
        month_cells.append(
            {
                "day": day,
                "date": current_date,
                "is_today": current_date == today,
                "items": exams_by_date.get(current_date, []),
            }
        )

    while len(month_cells) % 7 != 0:
        month_cells.append(None)

    calendar_rows = [
        month_cells[i : i + 7] for i in range(0, len(month_cells), 7)
    ]

    weekday_labels = ["Pzt", "Salı", "Çar", "Per", "Cum", "Cmt", "Paz"]

    upcoming_list = [
        exam for exam in serialized_exams if exam["scheduled_local"] and exam["scheduled_local"].date() >= today
    ][:6]

    return render(
        request,
        "eys/student_calendar.html",
        {
            "month_name": MONTH_LABELS[selected_month - 1],
            "selected_year": selected_year,
            "prev_month": {"month": prev_month, "year": prev_year},
            "next_month": {"month": next_month, "year": next_year},
            "weekday_labels": weekday_labels,
            "calendar_rows": calendar_rows,
            "has_events": any(cell and cell["items"] for cell in month_cells),
            "upcoming_list": upcoming_list,
        },
    )


def teacher_create_announcement(request):
    if not request.user.role or request.user.role.name not in TEACHER_ROLES:
        messages.error(request, "Sadece öğretim elemanları duyuru oluşturabilir.")
        return redirect("home")

    if request.method == "POST":
        form = AnnouncementForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.author = request.user
            ann.save()
            messages.success(request, "Duyuru öğrencilerle paylaşıldı.")
            return redirect("teacher_dashboard")
    else:
        form = AnnouncementForm(user=request.user)

    return render(
        request,
        "eys/teacher_create_announcement.html",
        {
            "form": form,
        },
    )


def global_search(request):
    if not request.user.is_authenticated:
        messages.info(request, "Arama yapabilmek için giriş yapmalısın.")
        return redirect("login")

    query = request.GET.get("q", "").strip()
    results_courses = []
    results_exams = []
    role_name = request.user.role.name if getattr(request.user, "role", None) else None

    if query:
        course_filter = Q(name__icontains=query) | Q(code__icontains=query)
        exam_filter = Q(name__icontains=query) | Q(description__icontains=query)

        if role_name == "Student":
            course_qs = request.user.courses_taken.filter(course_filter)
            exam_qs = Exam.objects.filter(course__in=request.user.courses_taken.all()).filter(exam_filter)
        elif role_name in TEACHER_ROLES:
            course_qs = request.user.courses_given.filter(course_filter)
            exam_qs = Exam.objects.filter(course__in=request.user.courses_given.all()).filter(exam_filter)
        else:
            course_qs = Course.objects.filter(course_filter)
            exam_qs = Exam.objects.filter(exam_filter)

        results_courses = course_qs.select_related("instructor")[:8]
        results_exams = exam_qs.select_related("course")[:8]

    context = {
        "query": query,
        "results_courses": results_courses,
        "results_exams": results_exams,
        "role_name": role_name,
    }
    return render(request, "eys/global_search.html", context)


def manage_exam_scores(request, exam_id):
    exam = get_object_or_404(
        Exam.objects.select_related("course__instructor"), id=exam_id, course__instructor=request.user
    )
    students = exam.course.students.all().order_by("first_name", "last_name", "username")
    existing = {
        res.student_id: res for res in ExamResult.objects.filter(exam=exam).select_related("student")
    }

    if request.method == "POST":
        if request.FILES.get("csv_file"):
            file = request.FILES["csv_file"]
            try:
                text = io.TextIOWrapper(file.file, encoding="utf-8")
            except Exception:
                text = io.StringIO(file.read().decode("utf-8", errors="ignore"))
            reader = csv.DictReader(text)
            errors = []
            processed = 0
            created_count = 0
            updated_count = 0
            deleted_count = 0
            for row in reader:
                sid = (row.get("student_id") or "").strip()
                username = (row.get("username") or "").strip()
                score_raw = (row.get("score") or "").strip()
                feedback = (row.get("feedback") or "").strip()
                student = None
                if sid.isdigit():
                    student = exam.course.students.filter(id=int(sid)).first()
                if not student and username:
                    student = exam.course.students.filter(username=username).first()
                if not student:
                    errors.append(f"Öğrenci bulunamadı: id={sid} username={username}")
                    continue
                processed += 1
                if score_raw == "":
                    if student.id in existing:
                        existing[student.id].delete()
                        deleted_count += 1
                    continue
                try:
                    score_val = float(score_raw.replace(",", "."))
                except ValueError:
                    errors.append(f"{student.get_full_name() or student.username} için skor değeri sayı olmalı.")
                    continue
                score_val = max(0, min(100, score_val))
                result, created = ExamResult.objects.get_or_create(
                    exam=exam,
                    student=student,
                    defaults={"score": score_val, "feedback": feedback},
                )
                if not created:
                    result.score = score_val
                    result.feedback = feedback
                    result.save()
                    updated_count += 1
                else:
                    created_count += 1

            if errors:
                for err in errors:
                    messages.error(request, err)
            else:
                messages.success(request, f"CSV içe aktarma tamamlandı. Toplam: {processed}, Yeni: {created_count}, Güncellenen: {updated_count}, Silinen: {deleted_count}.")
                return redirect("manage_exam_scores", exam_id=exam.id)

        errors = []
        for student in students:
            score_raw = request.POST.get(f"score_{student.id}", "").strip()
            feedback = request.POST.get(f"feedback_{student.id}", "").strip()

            if score_raw == "":
                if student.id in existing:
                    existing[student.id].delete()
                continue
            try:
                score_val = float(score_raw.replace(",", "."))
            except ValueError:
                errors.append(f"{student.get_full_name() or student.username} için skor değeri sayı olmalı.")
                continue

            score_val = max(0, min(100, score_val))
            result, created = ExamResult.objects.get_or_create(
                exam=exam,
                student=student,
                defaults={"score": score_val, "feedback": feedback},
            )
            if not created:
                result.score = score_val
                result.feedback = feedback
                result.save()

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            messages.success(request, "Sınav notları güncellendi.")
            return redirect("exam_detail", exam_id=exam.id)

    student_rows = [{"student": student, "result": existing.get(student.id)} for student in students]

    return render(
        request,
        "eys/teacher_manage_exam_scores.html",
        {
            "exam": exam,
            "student_rows": student_rows,
        },
    )

def export_exam_scores_csv(request, exam_id):
    exam = get_object_or_404(
        Exam.objects.select_related("course__instructor"), id=exam_id, course__instructor=request.user
    )
    students = exam.course.students.all().order_by("first_name", "last_name", "username")
    existing = {res.student_id: res for res in ExamResult.objects.filter(exam=exam).select_related("student")}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["student_id", "username", "full_name", "email", "score", "feedback"])
    for s in students:
        res = existing.get(s.id)
        writer.writerow([
            s.id,
            s.username,
            s.get_full_name() or "",
            s.email or "",
            res.score if res else "",
            res.feedback if res else "",
        ])
    resp = HttpResponse(output.getvalue(), content_type="text/csv")
    resp["Content-Disposition"] = f"attachment; filename=exam-{exam.id}-scores.csv"
    return resp

def teacher_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("user_login")
    courses = Course.objects.filter(instructor_id=request.user.id)
    course_ids = courses.values_list("id", flat=True)
    lo_total = LearningOutcome.objects.filter(course_id__in=course_ids).count()
    exam_total = Exam.objects.filter(course_id__in=course_ids).count()
    connection_total = ExamLOWeight.objects.filter(exam__course_id__in=course_ids).count()

    now = timezone.now()
    exams_qs = (
        Exam.objects.filter(course_id__in=course_ids, scheduled_at__isnull=False)
        .select_related("course")
        .order_by("scheduled_at")
    )
    upcoming_exams = [
        serialize_exam_for_student(exam, now)
        for exam in exams_qs
        if exam.scheduled_at and exam.scheduled_at >= now
    ][:5]

    announcement_qs = (
        Announcement.objects.filter(Q(course_id__in=course_ids) | Q(author=request.user))
        .select_related("course", "author")
        .order_by("-created_at")[:3]
    )
    announcement_cards = []
    for ann in announcement_qs:
        local_created = timezone.localtime(ann.created_at)
        month_label = MONTH_LABELS[local_created.month - 1]
        created_label = f"{local_created.day} {month_label} {local_created.year} · {local_created.strftime('%H:%M')}"
        author_name = (
            ann.author.get_full_name()
            if ann.author and ann.author.get_full_name()
            else getattr(ann.author, "username", "Sistem")
        )
        announcement_cards.append(
            {
                "id": ann.id,
                "title": ann.title,
                "body": ann.body,
                "attachment": ann.attachment,
                "meta": f"{author_name} • {created_label}",
                "course_label": f"{ann.course.code} · {ann.course.name}"
                if ann.course
                else "Genel Duyuru",
            }
        )

    # Bölüm Başkanı için Ekstra Veriler
    department_stats = None
    if request.user.role and request.user.role.name == "Head of Department":
        # 1. Akademik Personel Sayısı
        total_instructors = User.objects.filter(role__name__in=["Regular Instructor", "Advisor Instructor"]).count()
        
        # 2. Genel Başarı Ortalaması
        agg = ExamResult.objects.aggregate(avg_score=Avg("score"))
        avg_score = agg.get("avg_score") or 0
        
        # 3. Kritik Dersler (Ortalaması 50'nin altında olanlar)
        critical_count = 0
        all_courses = Course.objects.all()
        # Son eklenen 5 ders
        recent_courses = all_courses.order_by('-id')[:5]
        
        for crs in all_courses:
            c_avg = ExamResult.objects.filter(exam__course=crs).aggregate(a=Avg("score")).get("a")
            if c_avg and c_avg < 50:
                critical_count += 1

        department_stats = {
            "all_courses_count": all_courses.count(),
            "total_instructors": total_instructors,
            "average_score": round(avg_score, 1),
            "critical_course_count": critical_count,
            "recent_courses": recent_courses,
        }

    return render(
        request,
        "eys/teacher_dashboard.html",
        {
            "course_count": courses.count(),
            "lo_total": lo_total,
            "exam_total": exam_total,
            "connection_total": connection_total,
            "upcoming_exams": upcoming_exams,
            "announcement_cards": announcement_cards,
            "department_stats": department_stats,  # Yeni eklenen veri
        },
    )

@login_required
def affairs_dashboard(request):
    # İstatistikler
    student_count = User.objects.filter(role__name='Student').count()
    teacher_count = User.objects.filter(role__name__in=TEACHER_ROLES).count()
    course_count = Course.objects.count()
    
    # Son Duyurular (Global olanlar veya hepsi)
    recent_announcements = Announcement.objects.all().order_by('-created_at')[:5]
    
    context = {
        'student_count': student_count,
        'teacher_count': teacher_count,
        'course_count': course_count,
        'recent_announcements': recent_announcements,
    }
    return render(request, "eys/affairs_dashboard.html", context)

def teacher_courses(request):
    courses = (
        Course.objects.filter(instructor=request.user)
        .prefetch_related("learningoutcome_set", "exam_set", "students")
    )
    return render(request, "eys/teacher_courses.html", {"courses": courses})

@login_required
def edit_course_threshold(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.instructor != request.user:
        messages.error(request, "Bu ders için puan bantlarını sadece dersten sorumlu öğretim elemanı düzenleyebilir.")
        return redirect("course_detail", course_id=course.id)
    threshold = get_course_threshold(course)
    if request.method == "POST":
        form = CourseThresholdForm(request.POST, instance=threshold)
        if form.is_valid():
            form.save()
            messages.success(request, "Puan bantları güncellendi.")
            return redirect("course_detail", course_id=course.id)
    else:
        form = CourseThresholdForm(instance=threshold)
    return render(
        request,
        "eys/edit_course_threshold.html",
        {"form": form, "course": course},
    )

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    los = LearningOutcome.objects.filter(course=course).prefetch_related("examloweight_set__exam")
    exams = Exam.objects.filter(course=course).prefetch_related("examloweight_set__learning_outcome")
    materials_qs = CourseMaterial.objects.filter(course=course).order_by("week", "-created_at")
    weeks = sorted({m.week for m in materials_qs})
    try:
        selected_week = int(request.GET.get("week")) if request.GET.get("week") else None
    except ValueError:
        selected_week = None
    if selected_week:
        materials_qs = materials_qs.filter(week=selected_week)
    instructor = course.instructor
    if instructor:
        instructor_name = instructor.get_full_name() or instructor.username
    else:
        instructor_name = "Atanmad?"
    now = timezone.now()
    upcoming_exam_obj = (
        exams.filter(scheduled_at__isnull=False, scheduled_at__gte=now).order_by("scheduled_at").first()
    )
    upcoming_exam_label = (
        timezone.localtime(upcoming_exam_obj.scheduled_at).strftime("%d.%m.%Y ?? %H:%M")
        if upcoming_exam_obj
        else "Tarih bekleniyor"
    )

    announcement_qs = (
        Announcement.objects.filter(course=course)
        .select_related("author")
        .order_by("-pinned", "-created_at")[:6]
    )
    announcement_cards = []
    for ann in announcement_qs:
        created_local = timezone.localtime(ann.created_at)
        author_name = ann.author.get_full_name() if ann.author and ann.author.get_full_name() else getattr(ann.author, "username", "Sistem")
        initials = "".join([part[0] for part in author_name.split()[:2]]).upper() if author_name else "?"
        announcement_cards.append(
            {
                "id": ann.id,
                "title": ann.title,
                "body": ann.body,
                "attachment": ann.attachment,
                "author": author_name,
                "initials": initials,
                "timestamp": created_local.strftime("%d.%m.%Y ?? %H:%M"),
            }
        )

    threshold = get_course_threshold(course)
    threshold_values = threshold.as_dict()

    student_qs = (
        course.students.all()
        .select_related("role")
        .annotate(course_load=Count("courses_taken", distinct=True))
        .order_by("first_name", "last_name", "username")
    )
    exam_results = ExamResult.objects.filter(exam__course=course).select_related("student")
    results_by_student = defaultdict(list)
    for res in exam_results:
        try:
            results_by_student[res.student_id].append(float(res.score))
        except (TypeError, ValueError):
            continue
    student_cards = []
    for student in student_qs:
        full_name = student.get_full_name() or student.username
        initials = "".join([part[0] for part in full_name.split()[:2]]).upper() if full_name else student.username[:2].upper()
        last_login = (
            timezone.localtime(student.last_login).strftime("%d.%m.%Y ?? %H:%M")
            if student.last_login
            else "Hen?z giri? yapmad?"
        )
        date_joined = timezone.localtime(student.date_joined).strftime("%d.%m.%Y")
        scores = results_by_student.get(student.id, [])
        average_score = round(sum(scores) / len(scores), 2) if scores else None
        score_for_status = average_score if average_score is not None else 0

        if score_for_status >= threshold_values["stable_min"]:
            status = "?stikrarl?"
            status_color = "#1db954"
        elif score_for_status >= threshold_values["watch_min"]:
            status = "Takipte"
            status_color = "#ffb347"
        else:
            status = "Destek Gerekli"
            status_color = "#ff6b6b"

        if average_score is None:
            pass_label = "Hen?z not yok"
            display_score = "-"
        elif average_score >= threshold_values["pass_min"]:
            pass_label = "Ge?iyor"
            display_score = f"{average_score}"
        else:
            pass_label = "Ge?emeyebilir"
            display_score = f"{average_score}"

        student_cards.append(
            {
                "id": student.id,
                "name": full_name,
                "initials": initials,
                "email": student.email or "Belirtilmedi",
                "username": student.username,
                "last_login": last_login,
                "date_joined": date_joined,
                "course_load": student.course_load,
                "average_score": display_score,
                "status": status,
                "status_color": status_color,
                "pass_label": pass_label,
                "pass_min": threshold_values["pass_min"],
                "upcoming_exam": upcoming_exam_label,
            }
        )

    context = {
        "course": course,
        "los": los,
        "exams": exams,
        "announcement_cards": announcement_cards,
        "student_cards": student_cards,
        "materials": materials_qs,
        "weeks": weeks,
        "selected_week": selected_week,
        "upcoming_exam_label": upcoming_exam_label,
        "student_count": course.students.count(),
        "term_label": getattr(course, "term", None) or "Belirtilmedi",
        "instructor_name": instructor_name,
        "threshold": threshold,
    }
    return render(request, "eys/course_detail.html", context)

def add_lo(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = LOForm(request.POST)
        if form.is_valid():
            lo = form.save(commit=False)
            lo.course = course
            lo.save()
            messages.success(request, "LO başarıyla eklendi!")
            return redirect("course_detail", course_id=course.id)
    form = LOForm()
    return render(request, "eys/add_lo.html", {"form": form, "course": course})

def add_exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.course = course
            exam.save()
            messages.success(request, "Sınav başarıyla oluşturuldu!")
            return redirect("course_detail", course_id=course.id)
    else:
        form = ExamForm()
    return render(request, "eys/add_exam.html", {"form": form, "course": course})

def add_exam_lo_weight(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == "POST":
        form = ExamLOWeightForm(request.POST)
        if form.is_valid():
            weight = form.save(commit=False)
            weight.exam = exam
            weight.save()
            messages.success(request, "Learning Outcome bağlantısı kaydedildi!")
            return redirect("course_detail", course_id=exam.course.id)
    form = ExamLOWeightForm()
    form.fields['learning_outcome'].queryset = LearningOutcome.objects.filter(course=exam.course)
    return render(request, "eys/add_exam_lo_weight.html", {"form": form, "exam": exam})


def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    weights = ExamLOWeight.objects.filter(exam=exam)
    results = ExamResult.objects.filter(exam=exam).select_related("student")
    graded_count = results.count()
    avg_score = results.aggregate(avg=Avg("score"))["avg"] if graded_count else None
    student_total = exam.course.students.count() if exam.course else 0
    return render(
        request,
        "eys/exam_detail.html",
        {
            "exam": exam,
            "weights": weights,
            "results": results,
            "graded_count": graded_count,
            "average_score": avg_score,
            "student_total": student_total,
        },
    )
def teacher_calendar(request):
    now = timezone.localtime(timezone.now())
    today = timezone.localdate()

    try:
        selected_month = int(request.GET.get("month", now.month))
        selected_year = int(request.GET.get("year", now.year))
    except ValueError:
        selected_month = now.month
        selected_year = now.year

    if selected_month < 1 or selected_month > 12:
        selected_month = now.month
    if selected_year < 1900 or selected_year > 2100:
        selected_year = now.year

    def shift_month(year, month, delta):
        month += delta
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        return year, month

    prev_year, prev_month = shift_month(selected_year, selected_month, -1)
    next_year, next_month = shift_month(selected_year, selected_month, 1)

    view_mode = request.GET.get("view", "month").strip().lower()
    raw_ids = request.GET.getlist("course_id")
    selected_course_ids = []
    for rid in raw_ids:
        try:
            selected_course_ids.append(int(rid))
        except ValueError:
            pass

    courses = Course.objects.filter(instructor=request.user).order_by("code")
    exams_filter = {"scheduled_at__isnull": False, "course__in": courses}
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start_date = None
    end_date = None
    try:
        if start_raw:
            start_date = date.fromisoformat(start_raw)
        if end_raw:
            end_date = date.fromisoformat(end_raw)
    except ValueError:
        start_date = None
        end_date = None
    if start_date:
        exams_filter["scheduled_at__date__gte"] = start_date
    if end_date:
        exams_filter["scheduled_at__date__lte"] = end_date
    if selected_course_ids:
        exams_filter["course_id__in"] = selected_course_ids
    exams_qs = (
        Exam.objects.filter(**exams_filter)
        .select_related("course")
        .order_by("scheduled_at")
    )
    serialized_exams = [serialize_exam_for_student(exam, now) for exam in exams_qs]

    exams_by_date = defaultdict(list)
    for exam in serialized_exams:
        if exam["scheduled_local"]:
            exams_by_date[exam["scheduled_local"].date()].append(exam)

    weekday_labels = ["Pzt", "Salı", "Çar", "Per", "Cum", "Cmt", "Paz"]

    if view_mode == "week":
        week_date_str = request.GET.get("date")
        try:
            base_date = date.fromisoformat(week_date_str) if week_date_str else today
        except ValueError:
            base_date = today
        start_of_week = base_date - timedelta(days=base_date.weekday())
        week_days = []
        for i in range(7):
            d = start_of_week + timedelta(days=i)
            week_days.append(
                {
                    "date": d,
                    "label": f"{d.day} {MONTH_LABELS[d.month - 1]} {d.year}",
                    "weekday": weekday_labels[i],
                    "is_today": d == today,
                    "items": exams_by_date.get(d, []),
                }
            )
        prev_week = (start_of_week - timedelta(days=7)).isoformat()
        next_week = (start_of_week + timedelta(days=7)).isoformat()
        upcoming_list = [
            exam
            for exam in serialized_exams
            if exam["scheduled_local"] and exam["scheduled_local"].date() >= today
        ][:6]
        return render(
            request,
            "eys/teacher_calendar.html",
            {
                "view_mode": "week",
                "weekday_labels": weekday_labels,
                "week_days": week_days,
                "prev_week": prev_week,
                "next_week": next_week,
                "courses": courses,
                "selected_course_ids": selected_course_ids,
                "upcoming_list": upcoming_list,
                "start": start_date,
                "end": end_date,
            },
        )
    else:
        days_in_month = monthrange(selected_year, selected_month)[1]
        first_weekday = date(selected_year, selected_month, 1).weekday()

        month_cells = []
        for _ in range(first_weekday):
            month_cells.append(None)

        for day in range(1, days_in_month + 1):
            current_date = date(selected_year, selected_month, day)
            month_cells.append(
                {
                    "day": day,
                    "date": current_date,
                    "is_today": current_date == today,
                    "items": exams_by_date.get(current_date, []),
                }
            )

        while len(month_cells) % 7 != 0:
            month_cells.append(None)

        calendar_rows = [
            month_cells[i : i + 7] for i in range(0, len(month_cells), 7)
        ]

        upcoming_list = [
            exam
            for exam in serialized_exams
            if exam["scheduled_local"] and exam["scheduled_local"].date() >= today
        ][:6]

        return render(
            request,
            "eys/teacher_calendar.html",
            {
                "view_mode": "month",
                "month_name": MONTH_LABELS[selected_month - 1],
                "selected_year": selected_year,
                "prev_month": {"month": prev_month, "year": prev_year},
                "next_month": {"month": next_month, "year": next_year},
                "weekday_labels": weekday_labels,
                "calendar_rows": calendar_rows,
                "has_events": any(cell and cell["items"] for cell in month_cells),
                "upcoming_list": upcoming_list,
                "courses": courses,
                "selected_course_ids": selected_course_ids,
                "start": start_date,
                "end": end_date,
            },
        )

def teacher_calendar_ics(request):
    now = timezone.now()
    raw_ids = request.GET.getlist("course_id")
    selected_course_ids = []
    for rid in raw_ids:
        try:
            selected_course_ids.append(int(rid))
        except ValueError:
            pass

    courses = Course.objects.filter(instructor=request.user)
    exams_filter = {"scheduled_at__isnull": False, "course__in": courses}
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    try:
        if start_raw:
            exams_filter["scheduled_at__date__gte"] = date.fromisoformat(start_raw)
        if end_raw:
            exams_filter["scheduled_at__date__lte"] = date.fromisoformat(end_raw)
    except ValueError:
        pass
    if selected_course_ids:
        exams_filter["course_id__in"] = selected_course_ids
    exams_qs = Exam.objects.filter(**exams_filter).select_related("course").order_by("scheduled_at")

    include_assignments = request.GET.get("include_assignments") == "1"
    assignments_qs = []
    if include_assignments:
        assign_filter = {"due_at__isnull": False, "course__in": courses}
        try:
            if start_raw:
                assign_filter["due_at__date__gte"] = date.fromisoformat(start_raw)
            if end_raw:
                assign_filter["due_at__date__lte"] = date.fromisoformat(end_raw)
        except ValueError:
            pass
        if selected_course_ids:
            assign_filter["course_id__in"] = selected_course_ids
        assignments_qs = Assignment.objects.filter(**assign_filter).select_related("course").order_by("due_at")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//EYS//TeacherCalendar//TR",
        "X-WR-CALNAME:EYS Öğretmen Takvimi",
    ]
    for exam in exams_qs:
        if not exam.scheduled_at:
            continue
        start_utc = timezone.localtime(exam.scheduled_at, timezone.utc)
        end_utc = start_utc + timedelta(hours=1)
        uid = f"exam-{exam.id}@eys"
        summary = f"{exam.course.code} - {exam.name}"
        description = (exam.description or "").replace("\n", "\\n")
        url = reverse("exam_detail", args=[exam.id])
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}\\nURL:{url}",
            "END:VEVENT",
        ])
    for a in assignments_qs:
        if not a.due_at:
            continue
        start_utc = timezone.localtime(a.due_at, timezone.utc)
        end_utc = start_utc + timedelta(hours=1)
        uid = f"assignment-{a.id}@eys"
        summary = f"{a.course.code} - {a.title}"
        description = (a.description or "").replace("\n", "\\n")
        url = reverse("teacher_assignment_detail", args=[a.id])
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end_utc.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:Ödev - {summary}",
            f"DESCRIPTION:{description}\\nURL:{url}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    content = "\r\n".join(lines)
    resp = HttpResponse(content, content_type="text/calendar")
    resp["Content-Disposition"] = "attachment; filename=teacher-calendar.ics"
    return resp

@login_required
def edit_announcement(request, ann_id):
    ann = get_object_or_404(Announcement, id=ann_id)
    if ann.author != request.user:
        messages.error(request, "Bu duyuruyu düzenleme yetkiniz yok.")
        return redirect("teacher_dashboard")
    
    if request.method == "POST":
        form = AnnouncementForm(request.POST, request.FILES, instance=ann, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Duyuru başarıyla güncellendi.")
            return redirect("teacher_dashboard")
    else:
        form = AnnouncementForm(instance=ann, user=request.user)
        
    return render(request, "eys/edit_announcement.html", {"form": form, "ann": ann})

@login_required
def delete_announcement(request, ann_id):
    ann = get_object_or_404(Announcement, id=ann_id)
    if ann.author != request.user:
        messages.error(request, "Bu duyuruyu silme yetkiniz yok.")
        return redirect("teacher_dashboard")
    
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Duyuru başarıyla silindi.")
        return redirect("teacher_dashboard")
    
    return render(request, "eys/delete_announcement.html", {"ann": ann})

@login_required
def teacher_announcements(request):
    if not request.user.role or request.user.role.name not in TEACHER_ROLES:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")

    announcement_qs = Announcement.objects.filter(author=request.user).select_related("course").order_by("-pinned", "-created_at")

    grouped = defaultdict(list)
    for ann in announcement_qs:
        local_created = timezone.localtime(ann.created_at)
        date_key = local_created.date()
        month_label = MONTH_LABELS[local_created.month - 1]
        timestamp = f"{local_created.day} {month_label} {local_created.year} · {local_created.strftime('%H:%M')}"
        
        grouped[date_key].append(
            {
                "id": ann.id,
                "title": ann.title,
                "body": ann.body,
                "attachment": ann.attachment,
                "course_label": f"{ann.course.code} · {ann.course.name}" if ann.course else "Genel Duyuru",
                "timestamp": timestamp,
                "pinned": ann.pinned,
            }
        )

    timeline = []
    for day in sorted(grouped.keys(), reverse=True):
        month_label = MONTH_LABELS[day.month - 1]
        timeline.append(
            {
                "date_label": f"{day.day} {month_label} {day.year}",
                "items": grouped[day],
            }
        )

    return render(
        request,
        "eys/teacher_announcements.html",
        {
            "timeline": timeline,
            "total_count": announcement_qs.count(),
        },
    )

@login_required
def announcement_detail(request, ann_id):
    announcement = get_object_or_404(Announcement, id=ann_id)
    comments = announcement.comments.select_related('author', 'author__role').all()

    # Yetkilendirme: Öğrenciyse, kendi dersi mi veya genel duyuru mu?
    if request.user.role.name == 'Student':
        if announcement.course and announcement.course not in request.user.courses_taken.all():
            messages.error(request, "Bu duyuruyu görüntüleme yetkiniz yok.")
            return redirect('student_dashboard')
    
    # Yetkilendirme: Öğretmense, kendi dersi mi veya kendi duyurusu mu?
    elif request.user.role.name in TEACHER_ROLES:
        if announcement.course and announcement.course.instructor != request.user:
            if announcement.author != request.user:
                 messages.error(request, "Bu duyuruyu görüntüleme yetkiniz yok.")
                 return redirect('teacher_dashboard')

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.announcement = announcement
            new_comment.author = request.user
            new_comment.save()
            if announcement.author and announcement.author != request.user:
                url = reverse("announcement_detail", args=[announcement.id])
                create_notification(
                    announcement.author,
                    "announcement_comment",
                    f"{request.user.username} duyuruna yorum yaptı",
                    url=url,
                )
            messages.success(request, "Yorumunuz eklendi.")
            return redirect('announcement_detail', ann_id=announcement.id)
    else:
        comment_form = CommentForm()

    return render(request, 'eys/announcement_detail.html', {
        'announcement': announcement,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def teacher_assignments(request):
    if not request.user.role or request.user.role.name not in TEACHER_ROLES:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")
    assignments = (
        Assignment.objects.filter(course__instructor=request.user)
        .select_related("course")
        .order_by("-published_at", "-created_at")
    )
    templates = AssignmentTemplate.objects.filter(created_by=request.user)
    return render(
        request,
        "eys/teacher_assignments.html",
        {"assignments": assignments, "templates": templates},
    )


@login_required
def teacher_assignment_create(request):
    if not request.user.role or request.user.role.name not in TEACHER_ROLES:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")

    initial = {}
    try:
        preferred_course_id = int(request.GET.get("course_id"))
        course = Course.objects.filter(instructor=request.user, id=preferred_course_id).first()
        if course:
            initial["course"] = course
    except (TypeError, ValueError):
        pass
    template_id = request.GET.get("template_id")
    template_obj = None
    if template_id:
        template_obj = AssignmentTemplate.objects.filter(id=template_id, created_by=request.user).first()
        if template_obj:
            initial.update(
                {
                    "title": template_obj.title,
                    "description": template_obj.description,
                    "max_score": template_obj.max_score,
                }
            )

    if request.method == "POST":
        form = AssignmentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            if not assignment.published_at:
                assignment.published_at = timezone.now()
            assignment.save()
            # Kriterleri şablondan klonla
            if template_obj:
                for crit in template_obj.assignmentcriterion_set.all():
                    AssignmentCriterion.objects.create(
                        assignment=assignment,
                        title=crit.title,
                        max_score=crit.max_score,
                        order=crit.order,
                    )
            for student in assignment.course.students.all():
                url = reverse("student_assignment_detail", args=[assignment.id])
                create_notification(
                    student,
                    "new_assignment",
                    f"{assignment.course.code} için yeni ödev: {assignment.title}",
                    url=url,
                )
            messages.success(request, "Ödev kaydedildi.")
            return redirect("teacher_assignments")
    else:
        form = AssignmentForm(user=request.user, initial=initial)
    return render(request, "eys/teacher_assignment_form.html", {"form": form})


@login_required
def teacher_assignment_detail(request, assignment_id):
    assignment = get_object_or_404(
        Assignment.objects.select_related("course", "created_by"),
        id=assignment_id,
        course__instructor=request.user,
    )
    status_filter = request.GET.get("status", "").strip()
    submissions_qs = assignment.submissions.select_related("student").prefetch_related("attachments", "criterion_scores__criterion")
    if status_filter == "pending":
        submissions_qs = submissions_qs.filter(score__isnull=True)
    elif status_filter == "graded":
        submissions_qs = submissions_qs.filter(score__isnull=False)
    submissions = submissions_qs.order_by("-submitted_at")
    submitted_count = submissions.count()
    total_students = assignment.course.students.count()
    graded_count = submissions.exclude(score__isnull=True).count()
    avg_score = submissions.aggregate(avg=Avg("score"))["avg"] if graded_count else None
    scores = list(submissions.exclude(score__isnull=True).values_list("score", flat=True))
    min_score = min(scores) if scores else None
    max_score = max(scores) if scores else None
    median_score = None
    std_score = None
    if scores:
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        mid = n // 2
        if n % 2 == 0:
            median_score = (sorted_scores[mid - 1] + sorted_scores[mid]) / 2
        else:
            median_score = sorted_scores[mid]
        mean_val = float(avg_score) if avg_score is not None else 0
        variance = sum((float(s) - mean_val) ** 2 for s in sorted_scores) / n
        std_score = variance ** 0.5
    missing_students = assignment.course.students.exclude(id__in=submissions.values_list("student_id", flat=True))
    context = {
        "assignment": assignment,
        "submissions": submissions,
        "submitted_count": submitted_count,
        "total_students": total_students,
        "graded_count": graded_count,
        "average_score": avg_score,
        "min_score": min_score,
        "max_score": max_score,
        "median_score": median_score,
        "std_score": std_score,
        "missing_students": missing_students,
        "status_filter": status_filter,
        "criteria": assignment.criteria.all(),
    }
    return render(request, "eys/teacher_assignment_detail.html", context)


@login_required
def teacher_materials(request):
    if not request.user.role or request.user.role.name not in TEACHER_ROLES:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")
    materials = (
        CourseMaterial.objects.filter(course__instructor=request.user)
        .select_related("course")
        .order_by("course__code", "week", "-created_at")
    )
    return render(
        request,
        "eys/teacher_materials.html",
        {"materials": materials},
    )


@login_required
def create_material(request):
    if not request.user.role or request.user.role.name not in TEACHER_ROLES:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")
    initial = {}
    try:
        cid = int(request.GET.get("course_id"))
        course = Course.objects.filter(instructor=request.user, id=cid).first()
        if course:
            initial["course"] = course
            last_week = CourseMaterial.objects.filter(course=course).order_by("-week").first()
            if last_week:
                initial["week"] = last_week.week
    except (TypeError, ValueError):
        pass
    if request.method == "POST":
        form = CourseMaterialForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            mat = form.save(commit=False)
            mat.created_by = request.user
            mat.save()
            messages.success(request, "Materyal eklendi.")
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("teacher_materials")
    else:
        form = CourseMaterialForm(user=request.user, initial=initial)
    return render(request, "eys/create_material.html", {"form": form})


@login_required
def student_materials(request):
    if not request.user.role or request.user.role.name != "Student":
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")
    courses = list(request.user.courses_taken.all())
    if not courses:
        return render(request, "eys/student_materials.html", {"courses": [], "materials": []})
    try:
        selected_course_id = int(request.GET.get("course_id", courses[0].id))
    except ValueError:
        selected_course_id = courses[0].id
    selected_course = None
    for c in courses:
        if c.id == selected_course_id:
            selected_course = c
            break
    if selected_course is None:
        selected_course = courses[0]
    materials_qs = CourseMaterial.objects.filter(course=selected_course).order_by("week", "-created_at")
    weeks = sorted({m.week for m in materials_qs})
    try:
        selected_week = int(request.GET.get("week")) if request.GET.get("week") else None
    except ValueError:
        selected_week = None
    if selected_week:
        materials_qs = materials_qs.filter(week=selected_week)
    return render(
        request,
        "eys/student_materials.html",
        {
            "courses": courses,
            "selected_course": selected_course,
            "weeks": weeks,
            "selected_week": selected_week,
            "materials": materials_qs,
        },
    )


@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related("assignment", "assignment__course"),
        id=submission_id,
    )
    if submission.assignment.course.instructor != request.user:
        messages.error(request, "Bu teslimi notlama yetkiniz yok.")
        return redirect("home")

    criteria = list(submission.assignment.criteria.all())
    existing_scores = {
        sc.criterion_id: sc for sc in SubmissionCriterionScore.objects.filter(submission=submission)
    }
    if request.method == "POST":
        form = GradeSubmissionForm(request.POST, instance=submission, criteria=criteria)
        if form.is_valid():
            graded = form.save(commit=False)
            graded.graded_by = request.user
            graded.graded_at = timezone.now()
            graded.save()
            # Kriter bazlı puanları kaydet
            for crit in criteria:
                score_val = form.cleaned_data.get(f"criterion_{crit.id}")
                feedback_val = form.cleaned_data.get(f"criterion_{crit.id}_feedback")
                if score_val is None:
                    continue
                SubmissionCriterionScore.objects.update_or_create(
                    submission=submission,
                    criterion=crit,
                    defaults={"score": score_val, "feedback": feedback_val or ""},
                )
            url = reverse("student_assignment_detail", args=[submission.assignment.id])
            create_notification(
                submission.student,
                "submission_graded",
                f"{submission.assignment.title} ödevin notlandı",
                url=url,
            )
            messages.success(request, "Puan güncellendi.")
            return redirect("teacher_assignment_detail", assignment_id=submission.assignment.id)
    else:
        form = GradeSubmissionForm(instance=submission, criteria=criteria, existing_scores=existing_scores)
    return render(
        request,
        "eys/grade_submission.html",
        {"form": form, "submission": submission, "criteria": criteria},
    )


@login_required
def student_assignments(request):
    if not request.user.role or request.user.role.name != "Student":
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect("home")
    assignments_qs = Assignment.objects.filter(course__students=request.user, published_at__isnull=False).select_related("course").distinct()
    submission_map = {
        sub.assignment_id: sub
        for sub in Submission.objects.filter(assignment__in=assignments_qs, student=request.user)
    }
    upcoming = []
    past = []
    now = timezone.now()
    for assignment in assignments_qs:
        assignment.user_submission = submission_map.get(assignment.id)
        assignment.status_label = "Teslim edilmedi"
        if assignment.user_submission:
            if assignment.user_submission.score is not None:
                assignment.status_label = "Notlandı"
            else:
                assignment.status_label = "Teslim edildi"
        target_list = upcoming if (assignment.due_at and assignment.due_at >= now) else past
        target_list.append(assignment)
    upcoming = sorted(upcoming, key=lambda a: a.due_at or now)
    past = sorted(past, key=lambda a: a.due_at or now, reverse=True)
    return render(request, "eys/student_assignments.html", {"upcoming": upcoming, "past": past})


@login_required
def student_assignment_detail(request, assignment_id):
    assignment = get_object_or_404(
        Assignment.objects.select_related("course", "created_by"),
        id=assignment_id,
        course__students=request.user,
    )
    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    user_groups = assignment.groups.filter(members=request.user)
    initial_group = user_groups.first() if user_groups.exists() else None

    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission_obj = form.save(commit=False)
            submission_obj.assignment = assignment
            submission_obj.student = request.user
            if assignment.is_group:
                submission_obj.group = initial_group
            now = timezone.now()
            if assignment.due_at and now > assignment.due_at:
                messages.error(request, "Son teslim tarihi geçtiği için gönderilemedi.")
                return redirect("student_assignment_detail", assignment_id=assignment.id)
            submission_obj.version = (submission.version + 1) if submission else 1
            submission_obj.save()
            # Çoklu dosya ekleri
            files = request.FILES.getlist("attachments")
            for f in files:
                SubmissionAttachment.objects.create(
                    submission=submission_obj,
                    file=f,
                    version=submission_obj.version,
                )
            if assignment.course.instructor:
                url = reverse("teacher_assignment_detail", args=[assignment.id])
                create_notification(
                    assignment.course.instructor,
                    "submission_received",
                    f"{request.user.username} {assignment.title} ödevini teslim etti",
                    url=url,
                )
            messages.success(request, "Gönderimin kaydedildi.")
            return redirect("student_assignment_detail", assignment_id=assignment.id)
    else:
        form = SubmissionForm(instance=submission)

    return render(
        request,
        "eys/student_assignment_detail.html",
        {
            "assignment": assignment,
            "submission": submission,
            "form": form,
            "user_group": initial_group if assignment.is_group else None,
        },
    )


@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(
        request,
        "eys/notifications.html",
        {"notifications": notifs},
    )


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save(update_fields=["is_read", "read_at"])
    if notif.url:
        return redirect(notif.url)
    return redirect("notifications")


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    return redirect("notifications")


@login_required
def manage_assignment_criteria(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    if request.method == "POST":
        form = AssignmentCriterionForm(request.POST)
        if form.is_valid():
            crit = form.save(commit=False)
            crit.assignment = assignment
            crit.save()
            messages.success(request, "Kriter eklendi.")
            return redirect("manage_assignment_criteria", assignment_id=assignment.id)
    else:
        form = AssignmentCriterionForm()
    criteria = assignment.criteria.all()
    return render(
        request,
        "eys/manage_assignment_criteria.html",
        {"assignment": assignment, "form": form, "criteria": criteria},
    )


@login_required
def manage_assignment_groups(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    students_qs = assignment.course.students.all()
    if request.method == "POST":
        form = AssignmentGroupForm(request.POST, students_qs=students_qs)
        if form.is_valid():
            group = form.save(commit=False)
            group.assignment = assignment
            group.save()
            form.save_m2m()
            messages.success(request, "Grup kaydedildi.")
            return redirect("manage_assignment_groups", assignment_id=assignment.id)
    else:
        form = AssignmentGroupForm(students_qs=students_qs)
    groups = assignment.groups.prefetch_related("members")
    return render(
        request,
        "eys/manage_assignment_groups.html",
        {"assignment": assignment, "form": form, "groups": groups},
    )


@login_required
@login_required
def send_assignment_reminders(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    submitted_ids = assignment.submissions.values_list("student_id", flat=True)
    missing_students = assignment.course.students.exclude(id__in=submitted_ids)
    count = 0
    for student in missing_students:
        url = reverse("student_assignment_detail", args=[assignment.id])
        create_notification(
            student,
            "assignment_due",
            f"{assignment.title} ?devini teslim etmen gerekiyor.",
            url=url,
        )
        count += 1
    messages.success(request, f"Hatirlatma gonderildi ({count} ogrenci).")
    return redirect("teacher_assignment_detail", assignment_id=assignment.id)


@login_required
def send_exam_reminders(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, course__instructor=request.user)
    students = exam.course.students.all()
    count = 0
    for student in students:
        url = reverse("exam_detail", args=[exam.id])
        if exam.scheduled_at:
            date_label = timezone.localtime(exam.scheduled_at).strftime("%d.%m.%Y %H:%M")
        else:
            date_label = "Belirtilmedi"
        message = f"{exam.course.code} - {exam.name} sinavin yaklasiyor. Tarih: {date_label}"
        create_notification(
            student,
            "exam_reminder",
            message,
            url=url,
        )
        count += 1
    messages.success(request, f"Sinav hatirlatmasi gonderildi ({count} ogrenci).")
    return redirect("teacher_dashboard")

def export_submissions_csv(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    submissions = assignment.submissions.select_related("student")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="assignment-{assignment_id}-submissions.csv"'
    writer = csv.writer(response)
    writer.writerow(["Öğrenci", "Kullanıcı adı", "Puan", "Geri bildirim", "Gönderim Tarihi"])
    for sub in submissions:
        writer.writerow([
            sub.student.get_full_name() or sub.student.username,
            sub.student.username,
            sub.score or "",
            (sub.feedback or "").replace("\n", " "),
            timezone.localtime(sub.submitted_at).strftime("%d.%m.%Y %H:%M"),
        ])
    return response


@login_required
def export_submissions_zip(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    submissions = assignment.submissions.prefetch_related("attachments", "student")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for sub in submissions:
            for att in sub.attachments.all():
                filename = f"{sub.student.username}_v{att.version}_{att.file.name.split('/')[-1]}"
                with att.file.open("rb") as f:
                    zf.writestr(filename, f.read())
    resp = HttpResponse(buffer.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="assignment-{assignment_id}-submissions.zip"'
    return resp
