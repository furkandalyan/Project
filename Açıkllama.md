# 🎓 EYS - Eğitim Yönetim Sistemi
## Proje Dokümantasyonu ve Test Rehberi

---

## 📋 Proje Hakkında

**EYS (Eğitim Yönetim Sistemi)**, üniversitelerin akademik süreçlerini dijitalleştirmek için tasarlanmış kapsamlı bir web uygulamasıdır. Django framework'ü kullanılarak geliştirilmiş bu sistem, öğrenci kayıtlarından sınav notlarına, ders yönetiminden raporlamaya kadar tüm eğitim süreçlerini tek bir platform üzerinden yönetmeyi sağlar.

### 🎯 Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| **Rol Tabanlı Erişim** | Her kullanıcı türü için özelleştirilmiş dashboard ve yetkiler |
| **Ders Yönetimi** | Kurs oluşturma, öğrenci kayıt ve takibi |
| **Not Sistemi** | Sınav notları girişi, hesaplama ve raporlama |
| **Ödev Yönetimi** | Ödev oluşturma, teslim ve değerlendirme |
| **Akademik Takvim** | Ders programı ve etkinlik takibi |
| **Duyuru Sistemi** | Ders bazlı ve genel duyurular |
| **Gerçek Zamanlı İstatistikler** | Başarı oranları, sınıf ortalamaları ve risk analizleri |
| **Ders Materyalleri** | Haftalık içerik paylaşımı |

---

## 🔐 Test Kullanıcıları

> **⚠️ Önemli:** Tüm kullanıcıların şifresi: `123`

### 🎓 Öğrenciler

| Kullanıcı Adı | Ad Soyad | Açıklama |
|---------------|----------|----------|
| `ogrenci1` | Ali Yılmaz | 5 derse kayıtlı örnek öğrenci |
| `ogrenci2` | Ayşe Demir | Demo öğrenci |
| `ogrenci3` | Fatma Kara | Demo öğrenci |
| `ogrenci4` | Mehmet Ak | Demo öğrenci |
| `ogrenci5` | Zehra Yıldız | Demo öğrenci |

### 👨‍🏫 Öğretim Üyeleri

| Kullanıcı Adı | Ad Soyad | Rol | Verdiği Dersler |
|---------------|----------|-----|-----------------|
| `ogretmen1` | Ayşe Kaya | Öğretim Görevlisi | Fizik I, Matematik I |
| `ogretmen2` | Burak Yılmaz | Öğretim Görevlisi | Kimya I, Biyoloji I |
| `danisman1` | Mehmet Demir | Danışman | Bitirme Projesi |

### 👑 Yönetim Kadrosu

| Kullanıcı Adı | Ad Soyad | Rol | Yetkiler |
|---------------|----------|-----|----------|
| `baskan1` | Zeynep Şahin | Bölüm Başkanı | Tüm dersler, istatistikler, raporlar |
| `memur1` | Ahmet Memur | Öğrenci İşleri | Öğrenci kayıtları, transkript işlemleri |

---

## 🚀 Demo Senaryoları

### Senaryo 1: Öğrenci Girişi
1. `ogrenci1` / `123` ile giriş yapın
2. Dashboard'da ders listesi ve notları görüntüleyin
3. Akademik takvimi inceleyin
4. Ders materyallerine erişin

### Senaryo 2: Öğretmen Paneli
1. `ogretmen1` / `123` ile giriş yapın
2. Verdiğiniz derslerin listesini görün
3. Öğrenci not girişi yapın
4. Duyuru oluşturun

### Senaryo 3: Bölüm Başkanı Görünümü
1. `baskan1` / `123` ile giriş yapın
2. Tüm derslerin istatistiklerini inceleyin
3. Risk altındaki öğrencileri görüntüleyin
4. Genel raporları analiz edin

### Senaryo 4: Öğrenci İşleri
1. `memur1` / `123` ile giriş yapın
2. Öğrenci listelerini yönetin
3. Kayıt işlemlerini takip edin

---

## 💻 Teknik Mimari

---

### 🏗️ MTV Mimari Deseni (Model-Template-View)

Django, **MTV** (Model-Template-View) desenini kullanır. Bu, MVC'nin (Model-View-Controller) Django versiyonudur.

```
┌──────────────────────────────────────────────────────────────────┐
│                         KULLANICI                                 │
│                            │                                      │
│                            ▼                                      │
│                    ┌──────────────┐                               │
│                    │   TARAYICI   │ (Chrome, Firefox, Edge)       │
│                    └──────┬───────┘                               │
│                           │                                       │
│                           ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      DJANGO                                   │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  urls.py → Hangi URL hangi view'a gidecek?              │ │ │
│  │  │  Örnek: /login/ → user_login fonksiyonu                 │ │ │
│  │  └────────────────────────┬────────────────────────────────┘ │ │
│  │                           ▼                                   │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  views.py → İş mantığı burada (VIEW)                    │ │ │
│  │  │  - Kullanıcı doğrulama                                  │ │ │
│  │  │  - Veritabanından veri çekme                            │ │ │
│  │  │  - Hesaplamalar yapma                                   │ │ │
│  │  └────────────────────────┬────────────────────────────────┘ │ │
│  │                           │                                   │ │
│  │              ┌────────────┴────────────┐                     │ │
│  │              ▼                         ▼                     │ │
│  │  ┌─────────────────────┐   ┌─────────────────────────────┐   │ │
│  │  │  models.py (MODEL)  │   │  templates/*.html (TEMPLATE)│   │ │
│  │  │  - Veritabanı       │   │  - HTML sayfaları           │   │ │
│  │  │  - User, Course,    │   │  - CSS stilleri             │   │ │
│  │  │    Exam, vb.        │   │  - JavaScript               │   │ │
│  │  └─────────┬───────────┘   └──────────────┬──────────────┘   │ │
│  │            │                              │                   │ │
│  │            ▼                              │                   │ │
│  │  ┌─────────────────────┐                  │                   │ │
│  │  │   db.sqlite3        │                  │                   │ │
│  │  │   (Veritabanı)      │                  │                   │ │
│  │  └─────────────────────┘                  │                   │ │
│  │                                           ▼                   │ │
│  │                              ┌────────────────────────┐       │ │
│  │                              │  HTML Yanıtı           │       │ │
│  │                              │  (Kullanıcıya gönderil.│       │ │
│  │                              └────────────────────────┘       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

### 🔑 Kimlik Doğrulama Akışı (Authentication Flow)

Kullanıcı giriş yaptığında ne olur? Adım adım:

```
┌─────────────────────────────────────────────────────────────────┐
│  ADIM 1: Kullanıcı login sayfasına gelir                        │
│          URL: http://localhost:8000/login/                       │
│          ↓                                                       │
│  ADIM 2: Kullanıcı adı ve şifre girer                           │
│          Örnek: ogrenci1 / 123                                   │
│          ↓                                                       │
│  ADIM 3: Form POST edilir → views.py'deki user_login çalışır    │
│          ↓                                                       │
│  ADIM 4: Django authenticate() fonksiyonu çağrılır              │
│          - Kullanıcı adı veritabanında aranır                   │
│          - Şifre hash'i karşılaştırılır                         │
│          ↓                                                       │
│  ADIM 5: Başarılıysa → login() ile oturum açılır                │
│          ↓                                                       │
│  ADIM 6: Kullanıcının ROLÜ kontrol edilir                       │
│          ↓                                                       │
│  ADIM 7: Role göre yönlendirme yapılır:                         │
│          - Student        → /student/dashboard/                  │
│          - Instructor     → /teacher/dashboard/                  │
│          - Student Affairs → /affairs/dashboard/                 │
└─────────────────────────────────────────────────────────────────┘
```

**Kod Örneği (views.py):**
```python
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Django'nun authenticate fonksiyonu
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)  # Oturum aç
            
            # Role göre yönlendir
            if user.role.name == "Student":
                return redirect("student_dashboard")
            elif user.role.name == "Head of Department":
                return redirect("teacher_dashboard")
            # ... diğer roller
        else:
            messages.error(request, "Kullanıcı adı veya parola hatalı.")
    
    return render(request, "eys/login.html")
```

---

### 🗄️ Veritabanı Yapısı (Database Schema)

#### Model Nedir?

Model, veritabanındaki bir tabloyu temsil eden Python sınıfıdır. Her model bir tablo, her alan (field) bir sütundur.

**Örnek - User Modeli:**
```python
class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    
    # AbstractUser'dan gelen alanlar:
    # - username (kullanıcı adı)
    # - password (şifre - hash'lenmiş)
    # - email
    # - first_name, last_name
    # - is_active, is_staff, is_superuser
```

**Örnek - Course Modeli:**
```python
class Course(models.Model):
    name = models.CharField(max_length=100)      # Ders adı
    code = models.CharField(max_length=20)       # Ders kodu (FİZ101)
    instructor = models.ForeignKey(User, ...)    # Dersi veren hoca
    students = models.ManyToManyField(User, ...) # Kayıtlı öğrenciler
```

#### Veritabanı İlişkileri

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERİTABANI İLİŞKİLERİ                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐         │
│  │   Role   │◄────────│   User   │────────►│  Course  │         │
│  │          │  1:N    │          │   N:N   │          │         │
│  │ - name   │         │ - role   │         │ -instruc.│         │
│  └──────────┘         │ - name   │         │ -students│         │
│                       └────┬─────┘         └────┬─────┘         │
│                            │                    │               │
│                            │                    ▼               │
│                            │              ┌──────────┐          │
│                            │              │   Exam   │          │
│                            │              │ - course │          │
│                            │              │ - name   │          │
│                            │              └────┬─────┘          │
│                            │                   │                │
│                            ▼                   ▼                │
│                       ┌─────────────────────────────┐           │
│                       │       ExamResult            │           │
│                       │  - exam (FK)                │           │
│                       │  - student (FK)             │           │
│                       │  - score                    │           │
│                       └─────────────────────────────┘           │
│                                                                  │
│  FK = ForeignKey (Yabancı Anahtar) - 1:N ilişki                 │
│  N:N = ManyToMany - Çoka çok ilişki                             │
└─────────────────────────────────────────────────────────────────┘
```

#### Sistemdeki Tüm Modeller (18 adet)

| Model | Açıklama | Örnek Veri |
|-------|----------|------------|
| `Role` | Kullanıcı rolleri | Student, Head of Department |
| `User` | Kullanıcı bilgileri | ogrenci1, ogretmen1 |
| `Course` | Ders bilgileri | Fizik I (FİZ101) |
| `CourseThreshold` | Geçme notları | Min: 60, Orta: 65, İyi: 80 |
| `Exam` | Sınav bilgileri | Vize, Final |
| `ExamResult` | Sınav sonuçları | ogrenci1 - Vize: 75 |
| `LearningOutcome` | Öğrenme çıktıları | "Newton Kanunlarını açıklar" |
| `ExamLOWeight` | Sınav-çıktı ağırlıkları | Vize %40, Final %60 |
| `Assignment` | Ödev tanımları | Hafta 3 Ödevi |
| `Submission` | Ödev teslimleri | ogrenci1 teslim etti |
| `SubmissionAttachment` | Teslim dosyaları | odev.pdf |
| `AssignmentCriterion` | Değerlendirme kriterleri | İçerik: 50 puan |
| `SubmissionCriterionScore` | Kriter puanları | İçerik: 45/50 |
| `AssignmentGroup` | Grup ödevleri | Grup A |
| `AssignmentTemplate` | Ödev şablonları | Lab Raporu Şablonu |
| `Announcement` | Duyurular | "Vize tarihi değişti" |
| `AnnouncementComment` | Duyuru yorumları | "Anlaşıldı hocam" |
| `CourseMaterial` | Ders materyalleri | Hafta1_Sunum.pdf |

---

### 📂 Proje Dosya Yapısı

```
django-project/
│
├── manage.py                  # Django yönetim aracı
│                              # Kullanım: python manage.py <komut>
│
├── future/                    # Proje ayarları klasörü
│   ├── __init__.py
│   ├── settings.py           # ⭐ ANA AYAR DOSYASI
│   │                         # - Veritabanı bağlantısı
│   │                         # - Yüklü uygulamalar
│   │                         # - Güvenlik ayarları
│   ├── urls.py               # Ana URL yönlendirmeleri
│   ├── asgi.py               # ASGI yapılandırması
│   └── wsgi.py               # WSGI yapılandırması (production)
│
├── eys/                       # ⭐ ANA UYGULAMA
│   ├── __init__.py
│   ├── models.py             # 📊 Veritabanı modelleri (327 satır)
│   │                         # - User, Role, Course, Exam vb.
│   │
│   ├── views.py              # 🎯 İş mantığı (2012 satır)
│   │                         # - student_dashboard
│   │                         # - teacher_dashboard
│   │                         # - user_login, user_logout
│   │
│   ├── forms.py              # 📝 Form tanımları
│   │                         # - LoginForm, ExamForm vb.
│   │
│   ├── urls.py               # 🔗 URL yönlendirmeleri
│   │                         # - /student/*, /teacher/* vb.
│   │
│   ├── admin.py              # 👨‍💼 Admin panel ayarları
│   │
│   └── templates/eys/        # 🎨 HTML Şablonları (38 dosya)
│       ├── base.html         # Ana şablon (navbar, sidebar)
│       ├── login.html        # Giriş sayfası
│       │
│       ├── student_dashboard.html
│       ├── student_courses.html
│       ├── student_calendar.html
│       │
│       ├── teacher_dashboard.html
│       ├── teacher_courses.html
│       ├── teacher_assignments.html
│       │
│       └── affairs_dashboard.html
│
├── staticfiles/               # Statik dosyalar (CSS, JS, resimler)
│
├── db.sqlite3                 # 💾 VERİTABANI DOSYASI
│                              # - Tüm veriler burada saklanır
│                              # - GitHub'a YÜKLENMEZshort
│
├── requirements.txt           # Python bağımlılıkları
│                              # İçerik: Django>=5.0
│
└── run_scenario_direct.py     # 🎭 Test verisi oluşturucu
                               # - Kullanıcıları oluşturur
                               # - Dersleri oluşturur
                               # - Notları oluşturur
```

---

### 🔄 URL → View → Template Akışı

Bir sayfa nasıl yüklenir? Örnek: Öğrenci Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Kullanıcı tarayıcıda şu adrese gider:                       │
│     http://localhost:8000/student/dashboard/                     │
├─────────────────────────────────────────────────────────────────┤
│  2. urls.py dosyasında eşleşme aranır:                          │
│                                                                  │
│     path('student/dashboard/', views.student_dashboard,          │
│          name='student_dashboard')                               │
├─────────────────────────────────────────────────────────────────┤
│  3. views.py'deki student_dashboard fonksiyonu çalışır:         │
│                                                                  │
│     def student_dashboard(request):                              │
│         user = request.user                                      │
│         courses = user.courses_taken.all()  # Dersleri al        │
│         exams = ExamResult.objects.filter(student=user)          │
│                                                                  │
│         context = {                                              │
│             'courses': courses,                                  │
│             'exams': exams,                                      │
│             'average': calculate_average(exams),                 │
│         }                                                        │
│         return render(request, 'eys/student_dashboard.html',     │
│                       context)                                   │
├─────────────────────────────────────────────────────────────────┤
│  4. Template (student_dashboard.html) render edilir:            │
│                                                                  │
│     <h1>Hoş geldin, {{ user.first_name }}!</h1>                 │
│                                                                  │
│     <div class="stats">                                          │
│         <p>Ortalamanız: {{ average }}</p>                        │
│     </div>                                                       │
│                                                                  │
│     {% for course in courses %}                                  │
│         <div>{{ course.name }}</div>                             │
│     {% endfor %}                                                 │
├─────────────────────────────────────────────────────────────────┤
│  5. HTML yanıtı kullanıcının tarayıcısına gönderilir            │
└─────────────────────────────────────────────────────────────────┘
```

---

### 🔐 Rol Tabanlı Erişim Kontrolü

Sistemde 5 farklı kullanıcı rolü bulunur:

| Rol | Türkçe | Erişebildiği Sayfalar | Yetkiler |
|-----|--------|----------------------|----------|
| `Student` | Öğrenci | /student/* | Kendi notlarını görür, ödev teslim eder |
| `Regular Instructor` | Öğretmen | /teacher/* | Kendi derslerini yönetir, not girer |
| `Advisor Instructor` | Danışman | /teacher/* | + Danışmanlık işlemleri |
| `Head of Department` | Bölüm Başkanı | /teacher/* | TÜM dersleri görür, istatistikler |
| `Student Affairs` | Öğrenci İşleri | /affairs/* | Öğrenci kayıt işlemleri |

```
┌────────────────────────────────────────────────────────────────┐
│                    ROL KONTROL AKIŞI                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Kullanıcı giriş yaptı                                         │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ user.role.name  │                                            │
│  │ nedir?          │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│     ┌─────┼─────┬─────────┬─────────────┐                      │
│     ▼     │     ▼         ▼             ▼                      │
│ Student   │  Instructor  Head of    Student                    │
│     │     │     │        Department  Affairs                   │
│     ▼     │     ▼         ▼             ▼                      │
│ /student/ │  /teacher/  /teacher/   /affairs/                  │
│ dashboard │  dashboard  dashboard   dashboard                  │
│           │  (kendi     (TÜM        (kayıt                     │
│           │   dersleri)  dersler)    işleri)                   │
│           │                                                     │
└───────────┴─────────────────────────────────────────────────────┘
```

---

### 📊 İstatistik Hesaplama Örneği

Dashboard'da gösterilen istatistikler nasıl hesaplanır?

**views.py'den örnek kod:**
```python
def teacher_dashboard(request):
    user = request.user
    
    # Bölüm başkanı mı kontrol et
    is_hod = user.role and user.role.name == "Head of Department"
    
    if is_hod:
        # Bölüm başkanı TÜM dersleri görür
        courses = Course.objects.all()
    else:
        # Normal öğretmen sadece kendi derslerini görür
        courses = Course.objects.filter(instructor_id=user.id)
    
    # İstatistikleri hesapla
    total_students = User.objects.filter(role__name="Student").count()
    total_courses = courses.count()
    
    # Ortalama not hesaplama
    avg_score = ExamResult.objects.aggregate(Avg('score'))['score__avg']
    
    # Kritik öğrenciler (ortalaması 50'nin altında)
    critical_students = ExamResult.objects.filter(
        score__lt=50
    ).values('student').distinct().count()
    
    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'average_score': round(avg_score, 1) if avg_score else 0,
        'critical_count': critical_students,
    }
    
    return render(request, 'eys/teacher_dashboard.html', context)
```

---

### 🛠️ Kullanılan Teknolojiler (Detaylı)

| Teknoloji | Versiyon | Ne İçin Kullanılıyor? |
|-----------|----------|----------------------|
| **Python** | 3.13 | Ana programlama dili |
| **Django** | 5.x | Web framework - backend |
| **SQLite** | 3.x | Veritabanı (geliştirme için) |
| **HTML5** | - | Sayfa yapısı |
| **CSS3** | - | Sayfa stilleri, tasarım |
| **JavaScript** | ES6+ | Dinamik özellikler, grafikler |
| **Django ORM** | - | Veritabanı sorgulama |
| **Django Templates** | - | Dinamik HTML üretimi |
| **Django Auth** | - | Kimlik doğrulama, oturum yönetimi |
| **Django Messages** | - | Kullanıcıya bildirim gösterme |

---

## 🛠️ Yeni Bilgisayarda Kurulum

>  **ÇOK ÖNEMLİ - MUTLAKA OKUYUN!**
> 
> Projeyi GitHub'dan indirdiğinizde **veritabanı dosyası (db.sqlite3) gelmez!**
> 
> Bu demek oluyor ki:
> - ❌ Test kullanıcıları (ogrenci1, ogretmen1 vb.) **YOK**
> - ❌ Dersler, sınavlar, notlar **YOK**
> - ❌ Hiçbir veri **YOK**
>
> **Çözüm:** Aşağıdaki kurulum adımlarını **sırasıyla** uygulayın!

---

### 📥 Adım Adım Kurulum (Yeni Bilgisayar için)

**Adım 1:** Projeyi bilgisayarınıza indirin
```bash
git clone <GitHub-repo-linki>
cd django-project
```

**Adım 2:** Python bağımlılıklarını yükleyin
```bash
pip install django
```

**Adım 3:** Veritabanını oluşturun (boş tablolar oluşturur)
```bash
python manage.py migrate
```

**Adım 4:** Test verilerini yükleyin  **EN ÖNEMLİ ADIM**
```bash
python run_scenario_direct.py
```
> Bu komut çalıştıktan sonra tüm kullanıcılar, dersler ve notlar otomatik oluşturulur!

**Adım 5:** Sunucuyu başlatın
```bash
python manage.py runserver
```

**Adım 6:** Tarayıcıda açın: http://localhost:8000/login/

---

###  Her Şey Doğru mu Kontrol Edin

Kurulum başarılıysa şunları yapabilmelisiniz:
1. `ogrenci1` / `123` ile giriş yapabilirsiniz
2. Dashboard'da 5 ders görünür
3. Notlar ve istatistikler görüntülenir

---

###  Sunucuyu Çalıştırma (Sonraki Kullanımlarda)

Kurulumu bir kez yaptıktan sonra, sunucuyu başlatmak için sadece:

```bash
cd django-project
python manage.py runserver
```

**Erişim Adresi:** http://localhost:8000/login/

---

## 💡 Gelecekte Eklenebilecek Özellikler

> Bu bölüm, projeyi geliştirmek için fikir vermek amacıyla hazırlanmıştır.

### ⭐ Kolay Seviye (Başlangıç için ideal)

| Özellik | Tahmini Süre | Açıklama | Nasıl Yapılır? |
|---------|--------------|----------|----------------|
| **Şifre Değiştirme** | 1-2 saat | Kullanıcı kendi şifresini değiştirebilir | Django'nun `set_password()` fonksiyonu |
| **Profil Fotoğrafı** | 2-3 saat | Kullanıcı avatarı yükleyebilir | `ImageField` + dosya yükleme formu |
| **CSV Export** | 1-2 saat | Notları Excel'e aktarma | Python `csv` modülü |
| **Ders Arama** | 1 saat | Ders ismine göre arama | Django ORM `filter(name__icontains=...)` |
| **Son Görüntülenenler** | 2 saat | Son bakılan sayfaların listesi | Session kullanarak kaydetme |

//

---

### ⭐⭐ Orta Seviye (Biraz tecrübe gerektirir)

| Özellik | Tahmini Süre | Açıklama | Nasıl Yapılır? |
|---------|--------------|----------|----------------|
| **Karanlık Mod** | 3-4 saat | Tema değiştirme butonu | CSS değişkenleri + JavaScript toggle |
| **Not Grafiği** | 4-5 saat | Görsel başarı grafiği | Chart.js kütüphanesi |
| **Duyuru Bildirimi** | 3-4 saat | Yeni duyuru badge'i | Okunmamış duyuru sayacı |
| **Favori Dersler** | 3 saat | Dersleri favorilere ekleme | Yeni FavoriteCourse modeli |
| **Şifremi Unuttum** | 4-5 saat | Email ile şifre sıfırlama | Django `PasswordResetView` |

---

### ⭐⭐⭐ İleri Seviye (Proje büyütmek için)

| Özellik | Tahmini Süre | Açıklama |
|---------|--------------|----------|
| **Email Bildirimleri** | 1 gün | Ödev hatırlatma, not bildirimi |
| **Mobil Uygulama API** | 2-3 gün | REST API ile mobil entegrasyon |
| **Gerçek Zamanlı Bildirimler** | 2 gün | WebSocket ile anlık bildirimler |
| **PDF Transkript** | 1 gün | Öğrenci not dökümü PDF olarak |
| **Çoklu Dil Desteği** | 2 gün | Türkçe/İngilizce arayüz |

---

### 🛠️ Örnek Kod Parçaları

#### 1. Karanlık Mod (En Kolay)

**JavaScript (base.html'e ekle):**
```javascript
// Karanlık mod toggle butonu
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    // Tercihi kaydet
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Sayfa yüklendiğinde tercihi kontrol et
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}
```

**CSS (style.css'e ekle):**
```css
/* Karanlık mod stilleri */
body.dark-mode {
    background-color: #1a1a2e;
    color: #eaeaea;
}

body.dark-mode .sidebar {
    background-color: #16213e;
}

body.dark-mode .card {
    background-color: #0f3460;
}
```

---

#### 2. CSV Export (Not İndirme)

**views.py'e ekle:**
```python
import csv
from django.http import HttpResponse

def export_grades_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="notlar.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Öğrenci', 'Ders', 'Sınav', 'Not'])  # Başlık satırı
    
    results = ExamResult.objects.filter(student=request.user)
    for result in results:
        writer.writerow([
            result.student.get_full_name(),
            result.exam.course.name,
            result.exam.name,
            result.score
        ])
    
    return response
```

**urls.py'e ekle:**
```python
path('export/grades/', views.export_grades_csv, name='export_grades'),
```

---

#### 3. Not Grafiği (Chart.js)

**Template'e ekle:**
```html
<!-- Chart.js CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<canvas id="notChart" width="400" height="200"></canvas>

<script>
const ctx = document.getElementById('notChart').getContext('2d');
new Chart(ctx, {
    type: 'bar',  // veya 'line', 'pie'
    data: {
        labels: ['Fizik', 'Matematik', 'Kimya', 'Biyoloji'],
        datasets: [{
            label: 'Notlarım',
            data: [75, 82, 68, 90],  // Django'dan gelen veriler
            backgroundColor: [
                '#3b82f6',
                '#10b981',
                '#f59e0b',
                '#ef4444'
            ]
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true, max: 100 }
        }
    }
});
</script>
```

---

### 📚 Faydalı Kaynaklar

| Kaynak | Link | Açıklama |
|--------|------|----------|
| Django Dokümantasyon | https://docs.djangoproject.com | Resmi Django rehberi |
| Chart.js | https://www.chartjs.org | Grafik kütüphanesi |
| Bootstrap | https://getbootstrap.com | CSS framework |
| Django Girls Tutorial | https://tutorial.djangogirls.org/tr/ | Türkçe başlangıç rehberi |

---

*Bu dokümantasyon Aralık 2024'te hazırlanmıştır.*
