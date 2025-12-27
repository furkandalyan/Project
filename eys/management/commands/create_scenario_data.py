
from django.core.management.base import BaseCommand
from django.utils import timezone
from eys.models import (
    User, Role, Course, LearningOutcome, Exam, ExamLOWeight, 
    ExamResult, Announcement, Submission, Assignment
)
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Tutarlı test verisi oluşturur (Senaryo Bazlı)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Veritabani Temizleniyor...")
        
        # Manuel Temizlik
        # Sırayla silmek en iyisi (Foreign Key constraints)
        ExamResult.objects.all().delete()
        Exam.objects.all().delete()
        Course.objects.all().delete()
        User.objects.all().delete()
        Role.objects.all().delete()
        
        self.stdout.write("Senaryo Verisi Yukleniyor...")
        
        # 1. Rolleri Getir
        student_role, _ = Role.objects.get_or_create(name='Student')
        teacher_role, _ = Role.objects.get_or_create(name='Regular Instructor')
        advisor_role, _ = Role.objects.get_or_create(name='Advisor Instructor')
        head_role, _ = Role.objects.get_or_create(name='Head of Department')
        affairs_role, _ = Role.objects.get_or_create(name='Student Affairs')

        # 2. Kullanıcıları Oluştur
        def create_user(uname, role, fname, lname):
            u, created = User.objects.get_or_create(username=uname, defaults={
                'first_name': fname, 'last_name': lname, 'email': f'{uname}@univ.edu.tr', 'role': role
            })
            if created:
                u.set_password('123')
                u.save()
            return u

        student1 = create_user('ogrenci1', student_role, 'Ali', 'Yılmaz')
        teacher1 = create_user('ogretmen1', teacher_role, 'Ayşe', 'Kaya')
        advisor1 = create_user('danisman1', advisor_role, 'Mehmet', 'Demir')
        head1 = create_user('baskan1', head_role, 'Prof. Dr. Zeynep', 'Şahin')
        affairs1 = create_user('memur1', affairs_role, 'Ahmet', 'Memur')

        # 3. Dersler (Senaryo: 1 Başarılı, 1 Başarısız, 1 Orta)
        courses_config = [
            # Hoca: ogretmen1 (Başarılı Ders)
            {"code": "PHYS101", "name": "Fizik I", "teacher": teacher1, "avg_target": 85},
            # Hoca: ogretmen1 (Orta Ders)
            {"code": "MATH101", "name": "Matematik I", "teacher": teacher1, "avg_target": 65},
            # Hoca: danisman1 (Kritik/Başarısız Ders)
            {"code": "CENG401", "name": "Bitirme Projesi", "teacher": advisor1, "avg_target": 40}, 
        ]

        for conf in courses_config:
            course, _ = Course.objects.get_or_create(
                code=conf["code"],
                defaults={"name": conf["name"], "instructor": conf["teacher"]}
            )
            # Instructor güncelle (Fix)
            course.instructor = conf["teacher"]
            course.save()
            
            course.students.add(student1)
            
            # 4. Sınav ve Not (Vize)
            exam, _ = Exam.objects.get_or_create(
                course=course,
                name="Vize",
                defaults={
                    "description": "Vize Sınavı",
                    "scheduled_at": timezone.now() - timedelta(days=10)
                }
            )
            
            # Not Gir
            score = conf["avg_target"] + random.randint(-5, 5)
            # Notları biraz dağıtmak için extra öğrenci lazım ama şimdilik tek öğrenci var.
            # Tek öğrenci ile ortalama = öğrenci notu.
            
            res, _ = ExamResult.objects.get_or_create(
                exam=exam,
                student=student1,
                defaults={"score": score}
            )
            # Score güncelle (Scenario fix)
            res.score = score
            res.save()
            
            self.stdout.write(f"  * {course.code} - {exam.name}: {score} (Hedef: {conf['avg_target']})")

        self.stdout.write(self.style.SUCCESS("Senaryo Tamamlandi: Kritik Dersler ve Ortalamalar Hazir."))
