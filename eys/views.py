from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.utils import timezone

from .models import Course, LearningOutcome, Exam, ExamLOWeight, Announcement, ExamResult
from .forms import LOForm, ExamForm, ExamLOWeightForm, AnnouncementForm, ProfileUpdateForm

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


def serialize_exam_for_student(exam, now=None):
    now = now or timezone.now()
    scheduled_local = timezone.localtime(exam.scheduled_at) if exam.scheduled_at else None
    upcoming_window = now + timedelta(days=7)

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
                else "future"
            )
        ),
        "has_schedule": scheduled_local is not None,
        "day": scheduled_local.day if scheduled_local else None,
        "month": scheduled_local.month if scheduled_local else None,
        "year": scheduled_local.year if scheduled_local else None,
        "weekday_index": scheduled_local.weekday() if scheduled_local else None,
        "score": getattr(exam, "score", None),
    }

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role.name == "Student":
                return redirect("student_dashboard")
            if user.role.name in ["Regular Instructor", "Advisor Instructor", "Head of Department"]:
                return redirect("teacher_dashboard")
            if user.role.name == "Student Affairs":
                return redirect("affairs_dashboard")
        else:
            print("LOGIN FAILED:", username, password)
    return render(request, "eys/login.html", {"hide_navbar": True})

def user_logout(request):
    logout(request)
    return redirect("login")

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
                "title": ann.title,
                "body": ann.body,
                "meta": f"{author_name} • {created_label}",
                "course_label": f"{ann.course.code} · {ann.course.name}"
                if ann.course
                else "Genel Duyuru",
            }
        )
    if not announcement_cards:
        announcement_cards = [
            {
                "title": "Henüz duyuru yok",
                "meta": "Takipte kal",
                "body": "Öğretim elemanlarınız duyuru paylaştığında burada göreceksin.",
                "course_label": "",
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
    announcement_qs = (
        Announcement.objects.filter(Q(course__in=courses) | Q(course__isnull=True))
        .select_related("course", "author")
        .order_by("-created_at")
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
        form = AnnouncementForm(request.POST, user=request.user)
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

def teacher_dashboard(request):
    courses = Course.objects.filter(instructor=request.user)
    course_ids = courses.values_list("id", flat=True)
    lo_total = LearningOutcome.objects.filter(course_id__in=course_ids).count()
    exam_total = Exam.objects.filter(course_id__in=course_ids).count()
    connection_total = ExamLOWeight.objects.filter(exam__course_id__in=course_ids).count()
    return render(
        request,
        "eys/teacher_dashboard.html",
        {
            "course_count": courses.count(),
            "lo_total": lo_total,
            "exam_total": exam_total,
            "connection_total": connection_total,
        },
    )

def affairs_dashboard(request):
    return render(request, "eys/affairs_dashboard.html")

def teacher_courses(request):
    courses = (
        Course.objects.filter(instructor=request.user)
        .prefetch_related("learningoutcome_set", "exam_set", "students")
    )
    return render(request, "eys/teacher_courses.html", {"courses": courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    los = LearningOutcome.objects.filter(course=course).prefetch_related("examloweight_set__exam")
    exams = Exam.objects.filter(course=course).prefetch_related("examloweight_set__learning_outcome")
    instructor = course.instructor
    if instructor:
        instructor_name = instructor.get_full_name() or instructor.username
    else:
        instructor_name = "Atanmadı"
    now = timezone.now()
    upcoming_exam_obj = (
        exams.filter(scheduled_at__isnull=False, scheduled_at__gte=now).order_by("scheduled_at").first()
    )
    upcoming_exam_label = (
        timezone.localtime(upcoming_exam_obj.scheduled_at).strftime("%d.%m.%Y · %H:%M")
        if upcoming_exam_obj
        else "Tarih bekleniyor"
    )

    announcement_qs = (
        Announcement.objects.filter(course=course)
        .select_related("author")
        .order_by("-created_at")[:6]
    )
    announcement_cards = []
    for ann in announcement_qs:
        created_local = timezone.localtime(ann.created_at)
        author_name = ann.author.get_full_name() if ann.author and ann.author.get_full_name() else getattr(ann.author, "username", "Sistem")
        initials = "".join([part[0] for part in author_name.split()[:2]]).upper() if author_name else "?"
        announcement_cards.append(
            {
                "title": ann.title,
                "body": ann.body,
                "author": author_name,
                "initials": initials,
                "timestamp": created_local.strftime("%d.%m.%Y · %H:%M"),
            }
        )

    student_qs = (
        course.students.all()
        .select_related("role")
        .annotate(course_load=Count("courses_taken", distinct=True))
        .order_by("first_name", "last_name", "username")
    )
    past_exam_count = exams.filter(scheduled_at__lt=now).count()
    total_exams = exams.count()
    student_cards = []
    for student in student_qs:
        full_name = student.get_full_name() or student.username
        initials = "".join([part[0] for part in full_name.split()[:2]]).upper() if full_name else student.username[:2].upper()
        last_login = (
            timezone.localtime(student.last_login).strftime("%d.%m.%Y · %H:%M")
            if student.last_login
            else "Henüz giriş yapmadı"
        )
        date_joined = timezone.localtime(student.date_joined).strftime("%d.%m.%Y")
        activity_score = 50
        if student.last_login and student.last_login >= now - timedelta(days=7):
            activity_score += 15
        activity_score += min(15, student.course_load * 3)
        if total_exams:
            completion_ratio = past_exam_count / total_exams
            activity_score += int(completion_ratio * 20)
        activity_score = min(100, activity_score)
        if activity_score >= 80:
            status = "İstikrarlı"
            status_color = "#1db954"
        elif activity_score >= 65:
            status = "Takipte"
            status_color = "#ffb347"
        else:
            status = "Destek Gerekli"
            status_color = "#ff6b6b"

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
                "activity_score": activity_score,
                "status": status,
                "status_color": status_color,
                "upcoming_exam": upcoming_exam_label,
            }
        )

    context = {
        "course": course,
        "los": los,
        "exams": exams,
        "announcement_cards": announcement_cards,
        "student_cards": student_cards,
        "upcoming_exam_label": upcoming_exam_label,
        "student_count": course.students.count(),
        "term_label": getattr(course, "term", None) or "Belirtilmedi",
        "instructor_name": instructor_name,
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
