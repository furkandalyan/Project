from django.core.management.base import BaseCommand
from eys.models import Role, User


class Command(BaseCommand):
    help = 'Her rol için test kullanıcıları oluşturur'

    def handle(self, *args, **options):
        # Rolleri tanımla
        roles_data = [
            'Student',
            'Regular Instructor',
            'Advisor Instructor',
            'Head of Department',
            'Student Affairs',
        ]
        
        # Test kullanıcıları
        users_data = [
            {
                'username': 'ogrenci1',
                'password': 'test123',
                'first_name': 'Ahmet',
                'last_name': 'Yılmaz',
                'email': 'ahmet.yilmaz@ogrenci.edu.tr',
                'role_name': 'Student'
            },
            {
                'username': 'ogretmen1',
                'password': 'test123',
                'first_name': 'Mehmet',
                'last_name': 'Demir',
                'email': 'mehmet.demir@ogretmen.edu.tr',
                'role_name': 'Regular Instructor'
            },
            {
                'username': 'danisman1',
                'password': 'test123',
                'first_name': 'Ayşe',
                'last_name': 'Kaya',
                'email': 'ayse.kaya@ogretmen.edu.tr',
                'role_name': 'Advisor Instructor'
            },
            {
                'username': 'bolumbaskani',
                'password': 'test123',
                'first_name': 'Ali',
                'last_name': 'Çelik',
                'email': 'ali.celik@ogretmen.edu.tr',
                'role_name': 'Head of Department'
            },
            {
                'username': 'ogrenciisleri',
                'password': 'test123',
                'first_name': 'Fatma',
                'last_name': 'Şahin',
                'email': 'fatma.sahin@admin.edu.tr',
                'role_name': 'Student Affairs'
            },
        ]
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('🚀 Test Kullanıcıları Oluşturuluyor...'))
        self.stdout.write("=" * 60)
        self.stdout.write("")
        
        # 1. Rolleri oluştur
        self.stdout.write("📋 Roller oluşturuluyor...")
        created_roles = {}
        for role_name in roles_data:
            role, created = Role.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Oluşturuldu: {role_name}"))
            else:
                self.stdout.write(f"  ℹ️  Zaten var: {role_name}")
            created_roles[role.name] = role
        
        self.stdout.write("")
        
        # 2. Kullanıcıları oluştur
        self.stdout.write("👥 Kullanıcılar oluşturuluyor...")
        self.stdout.write("")
        
        for user_data in users_data:
            role = created_roles[user_data['role_name']]
            
            # Kullanıcı zaten varsa sil
            User.objects.filter(username=user_data['username']).delete()
            
            # Yeni kullanıcı oluştur
            user = User.objects.create_user(
                username=user_data['username'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                role=role
            )
            
            self.stdout.write(self.style.SUCCESS(f"  ✅ {user.get_full_name()} ({user.username})"))
            self.stdout.write(f"     └─ Rol: {role.name}")
            self.stdout.write(f"     └─ Email: {user.email}")
            self.stdout.write("")
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('✨ Tüm kullanıcılar başarıyla oluşturuldu!'))
        self.stdout.write("=" * 60)
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("📌 GİRİŞ BİLGİLERİ:"))
        self.stdout.write("-" * 60)
        self.stdout.write("")
        
        # Özet tablosu
        for user_data in users_data:
            self.stdout.write(f"🔹 {user_data['role_name']}")
            self.stdout.write(f"   Kullanıcı Adı: {user_data['username']}")
            self.stdout.write(f"   Şifre       : {user_data['password']}")
            self.stdout.write(f"   İsim        : {user_data['first_name']} {user_data['last_name']}")
            self.stdout.write("")
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.WARNING("💡 Not: Tüm şifreler 'test123' olarak ayarlandı"))
        self.stdout.write("=" * 60)
