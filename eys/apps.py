import sys
print("=" * 80, file=sys.stderr)
print("DEBUG: eys/apps.py is being loaded", file=sys.stderr)
print("=" * 80, file=sys.stderr)

from django.apps import AppConfig
print("DEBUG: AppConfig imported successfully", file=sys.stderr)


class EysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eys'
    
    def ready(self):
        print("=" * 80, file=sys.stderr)
        print("DEBUG: EysConfig.ready() called", file=sys.stderr)
        print(f"DEBUG: App name = {self.name}", file=sys.stderr)
        try:
            from .models import User
            print(f"DEBUG: User model accessible in ready(): {User}", file=sys.stderr)
            print(f"DEBUG: User._meta.db_table = {User._meta.db_table}", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG ERROR: Failed to import User in ready(): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
        print("=" * 80, file=sys.stderr)
