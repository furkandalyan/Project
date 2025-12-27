
import os
import django
import random
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "future.settings")
django.setup()

from django.utils import timezone
from eys.models import User, Role, Course, Exam, ExamResult

print("Cleaning DB...")
ExamResult.objects.all().delete()
Exam.objects.all().delete()
Course.objects.all().delete()
User.objects.all().delete()
Role.objects.all().delete()

print("Creating Roles...")
student_role, _ = Role.objects.get_or_create(name='Student')
teacher_role, _ = Role.objects.get_or_create(name='Regular Instructor')
advisor_role, _ = Role.objects.get_or_create(name='Advisor Instructor')
head_role, _ = Role.objects.get_or_create(name='Head of Department')
affairs_role, _ = Role.objects.get_or_create(name='Student Affairs')

def create_user(uname, role, fname, lname):
    u, created = User.objects.get_or_create(username=uname, defaults={
        'first_name': fname, 'last_name': lname, 'email': f'{uname}@univ.edu.tr', 'role': role
    })
    if created:
        u.set_password('123')
        u.save()
    return u

print("Creating Users...")
# Tekil Kullanıcılar
teacher1 = create_user('ogretmen1', teacher_role, 'Ayse', 'Kaya')
teacher2 = create_user('ogretmen2', teacher_role, 'Burak', 'Yilmaz')
advisor1 = create_user('danisman1', advisor_role, 'Mehmet', 'Demir')
head1 = create_user('baskan1', head_role, 'Zeynep', 'Sahin')
affairs1 = create_user('memur1', affairs_role, 'Ahmet', 'Memur')

# Öğrenci Grubu
students = []
for i in range(1, 6): # 5 Öğrenci
    s = create_user(f'ogrenci{i}', student_role, f'Ogrenci', f'{i}')
    students.append(s)

print("Creating Courses...")
courses_config = [
    # Hoca 1 (Ayşe)
    {"code": "PHYS101", "name": "Fizik I", "teacher": teacher1, "avg_target": 80},
    {"code": "MATH101", "name": "Matematik I", "teacher": teacher1, "avg_target": 60},
    # Hoca 2 (Burak)
    {"code": "CHEM101", "name": "Kimya I", "teacher": teacher2, "avg_target": 75},
    {"code": "BIO101", "name": "Biyoloji I", "teacher": teacher2, "avg_target": 90},
    # Danışman Hoca
    {"code": "CENG401", "name": "Bitirme Projesi", "teacher": advisor1, "avg_target": 45}, # Kritik
]

for conf in courses_config:
    course, _ = Course.objects.get_or_create(
        code=conf["code"],
        defaults={"name": conf["name"], "instructor": conf["teacher"]}
    )
    course.instructor = conf["teacher"]
    course.save()
    
    # Tüm öğrencileri derse kaydet
    for s in students:
        course.students.add(s)
    
    # Sınav Oluştur
    exam, _ = Exam.objects.get_or_create(
        course=course,
        name="Vize",
        defaults={
            "description": "Vize Sinavi",
            "scheduled_at": timezone.now() - timedelta(days=10)
        }
    )
    
    # Notları Gir
    course_scores = []
    for s in students:
        # Varyasyon: Target +/- 15 puan
        score = max(0, min(100, conf["avg_target"] + random.randint(-15, 15)))
        res, _ = ExamResult.objects.get_or_create(
            exam=exam,
            student=s,
            defaults={"score": score}
        )
        res.score = score
        res.save()
        course_scores.append(score)
    
    avg = sum(course_scores) / len(course_scores)
    print(f"Created: {course.code} - Avg: {avg:.1f} (Target: {conf['avg_target']})")

print("Done.")
