from django.core.management.base import BaseCommand
from eys.models import User


class Command(BaseCommand):
    help = 'Creates an admin superuser with username "admin" and password "admin"'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin'
        
        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists. Deleting and recreating...'))
            User.objects.filter(username=username).delete()
        
        # Create superuser
        admin_user = User.objects.create_superuser(
            username=username,
            password=password,
            email='admin@example.com',
            first_name='Admin',
            last_name='User'
        )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Admin user created successfully!'))
        self.stdout.write(f'   Username: {username}')
        self.stdout.write(f'   Password: {password}')
        self.stdout.write(self.style.WARNING('⚠️  Please change the password in production!'))

