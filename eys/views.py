from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Course, LearningOutcome, Exam, ExamLOWeight
from .forms import LOForm, ExamForm, ExamLOWeightForm

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
    courses = request.user.courses_taken.all().prefetch_related("learningoutcome_set", "exam_set")
    lo_qs = LearningOutcome.objects.filter(course__in=courses)
    exams_qs = Exam.objects.filter(course__in=courses)

    sample_los = list(lo_qs[:4])
    if not sample_los:
        lo_success_data = [
            {"label": "LO 1", "percent": 80},
            {"label": "LO 2", "percent": 65},
            {"label": "LO 3", "percent": 92},
        ]
    else:
        lo_success_data = []
        base_values = [82, 68, 91, 74]
        for idx, lo in enumerate(sample_los):
            lo_success_data.append(
                {
                    "label": lo.title or f"LO {lo.id}",
                    "percent": base_values[idx % len(base_values)],
                }
            )

    exam_results = []
    for exam in exams_qs[:5]:
        exam_results.append(
            {
                "name": exam.name,
                "score": None,
            }
        )
    if not exam_results:
        exam_results = [
            {"name": "Vize", "score": 80},
            {"name": "Final", "score": None},
            {"name": "Quiz 1", "score": None},
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
        },
    )

def student_courses(request):
    courses = (
        request.user.courses_taken.all()
        .select_related("instructor")
        .prefetch_related("learningoutcome_set", "exam_set")
    )
    return render(request, "eys/student_courses.html", {"courses": courses})


def student_course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("instructor"), id=course_id, students=request.user
    )
    los = LearningOutcome.objects.filter(course=course).prefetch_related("examloweight_set__exam")
    exams = Exam.objects.filter(course=course).prefetch_related("examloweight_set__learning_outcome")
    context = {
        "course": course,
        "los": los,
        "exams": exams,
        "student_count": course.students.count(),
        "term_label": getattr(course, "term", None) or "Belirtilmedi",
        "instructor_name": course.instructor.get_full_name()
        if course.instructor and course.instructor.get_full_name()
        else getattr(course.instructor, "username", "Atanmadı"),
    }
    return render(request, "eys/student_course_detail.html", context)


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
    context = {
        "course": course,
        "los": los,
        "exams": exams,
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
    return render(request, "eys/exam_detail.html", {"exam": exam, "weights": weights})
