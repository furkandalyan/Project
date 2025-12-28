print("=" * 80)
print("DEBUG: eys/apps.py is being loaded")
print("=" * 80)

from django.apps import AppConfig
print("DEBUG: AppConfig imported successfully")


class EysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eys'
    
    def ready(self):
        print("=" * 80)
        print("DEBUG: EysConfig.ready() called")
        print(f"DEBUG: App name = {self.name}")
        try:
            from .models import User
            print(f"DEBUG: User model accessible in ready(): {User}")
            print(f"DEBUG: User._meta.db_table = {User._meta.db_table}")
            print(f"DEBUG: User._meta.verbose_name = {User._meta.verbose_name}")
            print(f"DEBUG: User._meta.verbose_name_plural = {User._meta.verbose_name_plural}")
            
            # Check if User is in admin registry
            from django.contrib import admin
            if User in admin.site._registry:
                print(f"DEBUG: ✓ User model is in admin registry in ready()")
                print(f"DEBUG: User admin class = {admin.site._registry[User]}")
            else:
                print(f"DEBUG: ✗ WARNING: User model NOT in admin registry in ready()!")
                print(f"DEBUG: Current registry keys = {list(admin.site._registry.keys())}")
        except Exception as e:
            print(f"DEBUG ERROR: Failed to import User in ready(): {e}")
            import traceback
            traceback.print_exc()
        print("=" * 80)
