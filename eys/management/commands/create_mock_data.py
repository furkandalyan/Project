from django.core.management.base import BaseCommand
from django.utils import timezone
from eys.models import (
    User, Role, Course, LearningOutcome, Exam, ExamLOWeight, 
    ExamResult, Announcement, Submission, Assignment
)
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sistemi test etmek için gerçekçi veriler üretir'

    def handle(self, *args, **kwargs):
        self.stdout.write("🎲 Mock Data Üretimi Başlıyor...")

        # 1. Hocaları ve Öğrenciyi Bul
        try:
            student = User.objects.get(username='ogrenci1')
            instructor = User.objects.get(username='ogretmen1')
            advisor = User.objects.get(username='danisman1')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Önce 'python manage.py create_test_users' komutunu çalıştırın!"))
            return

        # 2. Dersler Oluştur (Bilgisayar Müh. Müfredatı)
        courses_data = [
            {"code": "CENG101", "name": "Algoritma ve Programlama I", "desc": "C dili ile programlamaya giriş.", "teacher": instructor},
            {"code": "CENG201", "name": "Veri Yapıları", "desc": "Linked List, Stack, Queue, Tree yapıları.", "teacher": instructor},
            {"code": "CENG301", "name": "Veritabanı Yönetim Sistemleri", "desc": "SQL, Normalizasyon ve DB Tasarımı.", "teacher": instructor},
            {"code": "CENG401", "name": "Bitirme Projesi I", "desc": "Mühendislik tasarımı ve proje geliştirme.", "teacher": advisor}
        ]

        created_courses = []
        for c_data in courses_data:
            course, created = Course.objects.get_or_create(
                code=c_data["code"],
                defaults={
                    "name": c_data["name"],
                    "instructor": c_data["teacher"],
                }
            )
            # Eğer ders varsa bile instructor'ı güncelle (Mock data fix için)
            if not created: 
                course.instructor = c_data["teacher"]
                course.save()

            # Öğrenciyi derse kaydet
            course.students.add(student)
            created_courses.append(course)
            self.stdout.write(f"  📚 Ders: {course.code}")

        # 3. Learning Outcomes (Öğrenim Çıktıları)
        lo_samples = {
            "CENG101": ["Değişkenleri kullanabilir", "Döngüleri kurabilir", "Fonksiyon yazabilir"],
            "CENG201": ["Ağaç yapılarını analiz eder", "Sıralama algoritmalarını karşılaştırır"],
            "CENG301": ["ER Diyagramı çizebilir", "Karmaşık SQL sorguları yazar", "Normalizasyon yapar"],
            "CENG401": ["Proje planı hazırlar", "Takım çalışması yapar"]
        }

        for course in created_courses:
            los = lo_samples.get(course.code, [])
            for desc in los:
                lo, _ = LearningOutcome.objects.get_or_create(
                    course=course,
                    title=desc,  # description yerine title kullanılıyor modelde
                    defaults={"description": desc}
                )

        # 4. Sınavlar ve Notlar
        exam_types = ["Vize", "Final", "Quiz 1", "Proje"]
        
        for course in created_courses:
            # Her derse 2-3 sınav ekle
            num_exams = random.randint(2, 3)
            current_exams = random.sample(exam_types, num_exams)
            
            for ex_name in current_exams:
                # Sınav Tarihi (Geçmiş veya Gelecek)
                days_diff = random.randint(-20, 10) # 20 gün önce ile 10 gün sonrası arası
                exam_date = timezone.now() + timedelta(days=days_diff)
                
                exam, created = Exam.objects.get_or_create(
                    course=course,
                    name=ex_name,
                    defaults={
                        "description": f"{course.name} dersi için {ex_name} sınavı.",
                        "scheduled_at": exam_date,
                        # date, duration, max_score kaldırıldı
                    }
                )

                # LO Bağlantısı (Rastgele ağırlıklar)
                course_los = LearningOutcome.objects.filter(course=course)
                if course_los.exists():
                    # Rastgele 1-2 LO seç ve bağla
                    selected_los = random.sample(list(course_los), min(len(course_los), 2))
                    weight_per_lo = 100 // len(selected_los)
                    for lo in selected_los:
                        ExamLOWeight.objects.get_or_create(
                            exam=exam,
                            learning_outcome=lo,
                            defaults={"weight": weight_per_lo}
                        )

                # Not Girişi (Sadece geçmiş sınavlar için)
                if days_diff < 0:
                    score = random.randint(45, 100)
                    ExamResult.objects.get_or_create(
                        exam=exam,
                        student=student,
                        defaults={"score": score}
                    )
                    self.stdout.write(f"    📝 Not Girildi: {course.code} - {ex_name}: {score}")

        # 5. Duyurular
        announcements = [
            ("Vize Tarihleri Hakkında", "Arkadaşlar vize tarihleri takvime işlendi, başarılar.", created_courses[0]),
            ("Ders İptali", "Bugünkü dersim sağlık nedenleriyle iptal olmuştur.", created_courses[1]),
            ("Proje Teslimi", "Projelerinizi sisteme yüklemeyi unutmayın.", created_courses[2]),
        ]

        for title, body, course in announcements:
            Announcement.objects.get_or_create(
                title=title,
                defaults={
                    "body": body,
                    "course": course,
                    "author": instructor
                }
            )

        self.stdout.write(self.style.SUCCESS("✅ Mock Data başarıyla oluşturuldu!"))
