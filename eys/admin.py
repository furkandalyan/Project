import sys
print("=" * 80, file=sys.stderr)
print("DEBUG: eys/admin.py is being loaded", file=sys.stderr)
print("=" * 80, file=sys.stderr)

from django.contrib import admin
print("DEBUG: django.contrib.admin imported successfully", file=sys.stderr)

from django.contrib.auth.admin import UserAdmin
print("DEBUG: UserAdmin imported successfully", file=sys.stderr)

print("DEBUG: Attempting to import models...", file=sys.stderr)
try:
    from .models import (
        Role,
        User,
        Course,
        CourseThreshold,
        Exam,
        LearningOutcome,
        ExamLOWeight,
        Announcement,
        ExamResult,
    )
    print("DEBUG: All models imported successfully", file=sys.stderr)
    print(f"DEBUG: User model = {User}", file=sys.stderr)
    print(f"DEBUG: User model type = {type(User)}", file=sys.stderr)
    print(f"DEBUG: User._meta.app_label = {User._meta.app_label}", file=sys.stderr)
    print(f"DEBUG: User._meta.model_name = {User._meta.model_name}", file=sys.stderr)
    print(f"DEBUG: User._meta.db_table = {User._meta.db_table}", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to import models: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise

print("DEBUG: Creating CustomUserAdmin class...", file=sys.stderr)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "role")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )

    search_fields = ("username",)
    ordering = ("username",)

print("DEBUG: CustomUserAdmin class created", file=sys.stderr)
print(f"DEBUG: CustomUserAdmin.model = {CustomUserAdmin.model}", file=sys.stderr)

print("DEBUG: Checking admin.site state...", file=sys.stderr)
print(f"DEBUG: admin.site = {admin.site}", file=sys.stderr)
print(f"DEBUG: admin.site._registry = {admin.site._registry}", file=sys.stderr)

print("DEBUG: Registering User model...", file=sys.stderr)
try:
    admin.site.register(User, CustomUserAdmin)
    print(f"DEBUG: User registered successfully", file=sys.stderr)
    print(f"DEBUG: admin.site._registry after User registration = {list(admin.site._registry.keys())}", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register User: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering Role model...", file=sys.stderr)
try:
    admin.site.register(Role)
    print(f"DEBUG: Role registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Role: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering Course model...", file=sys.stderr)
try:
    admin.site.register(Course)
    print(f"DEBUG: Course registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Course: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering CourseThreshold model...", file=sys.stderr)
try:
    admin.site.register(CourseThreshold)
    print(f"DEBUG: CourseThreshold registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register CourseThreshold: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering Exam model...", file=sys.stderr)
try:
    admin.site.register(Exam)
    print(f"DEBUG: Exam registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Exam: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering LearningOutcome model...", file=sys.stderr)
try:
    admin.site.register(LearningOutcome)
    print(f"DEBUG: LearningOutcome registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register LearningOutcome: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering ExamLOWeight model...", file=sys.stderr)
try:
    admin.site.register(ExamLOWeight)
    print(f"DEBUG: ExamLOWeight registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register ExamLOWeight: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering Announcement model...", file=sys.stderr)
try:
    admin.site.register(Announcement)
    print(f"DEBUG: Announcement registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Announcement: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Registering ExamResult model...", file=sys.stderr)
try:
    admin.site.register(ExamResult)
    print(f"DEBUG: ExamResult registered successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG ERROR: Failed to register ExamResult: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("DEBUG: Final admin.site._registry =", file=sys.stderr)
for model, admin_class in admin.site._registry.items():
    print(f"DEBUG:   - {model} -> {admin_class}", file=sys.stderr)

print("=" * 80, file=sys.stderr)
print("DEBUG: eys/admin.py loading complete", file=sys.stderr)
print("=" * 80, file=sys.stderr)
