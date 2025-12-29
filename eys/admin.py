print("=" * 80)
print("DEBUG: eys/admin.py is being loaded")
print("=" * 80)

from django.contrib import admin
print("DEBUG: django.contrib.admin imported successfully")

from django.contrib.auth.admin import UserAdmin
print("DEBUG: UserAdmin imported successfully")

print("DEBUG: Attempting to import models...")
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
    print("DEBUG: All models imported successfully")
    print(f"DEBUG: User model = {User}")
    print(f"DEBUG: User model type = {type(User)}")
    print(f"DEBUG: User._meta.app_label = {User._meta.app_label}")
    print(f"DEBUG: User._meta.model_name = {User._meta.model_name}")
    print(f"DEBUG: User._meta.db_table = {User._meta.db_table}")
except Exception as e:
    print(f"DEBUG ERROR: Failed to import models: {e}")
    import traceback
    traceback.print_exc()
    raise

print("DEBUG: Creating CustomUserAdmin class...")
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "role", "advisor", "is_staff", "is_active")
    list_filter = ("role", "advisor", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "role", "advisor")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "role", "advisor", "is_staff", "is_active"),
        }),
    )

    search_fields = ("username",)
    ordering = ("username",)

print("DEBUG: CustomUserAdmin class created")
print(f"DEBUG: CustomUserAdmin.model = {CustomUserAdmin.model}")

print("DEBUG: Checking admin.site state...")
print(f"DEBUG: admin.site = {admin.site}")
print(f"DEBUG: admin.site._registry = {admin.site._registry}")

# Unregister default User model if it exists (from django.contrib.auth)
print("DEBUG: Checking if default User model is registered...")
try:
    from django.contrib.auth.models import User as DefaultUser
    if DefaultUser in admin.site._registry:
        print(f"DEBUG: Default User model found in registry, unregistering...")
        admin.site.unregister(DefaultUser)
        print(f"DEBUG: Default User model unregistered successfully")
    else:
        print(f"DEBUG: Default User model not in registry (this is expected with custom User model)")
except Exception as e:
    print(f"DEBUG: Could not check/unregister default User: {e}")

print("DEBUG: Registering custom User model...")
try:
    admin.site.register(User, CustomUserAdmin)
    print(f"DEBUG: User registered successfully")
    print(f"DEBUG: admin.site._registry after User registration = {list(admin.site._registry.keys())}")
    
    # Verify User is in registry
    if User in admin.site._registry:
        print("DEBUG: User model confirmed in admin registry")
        print(f"DEBUG: User admin class = {admin.site._registry[User]}")
    else:
        print(f"DEBUG: ✗ ERROR: User model NOT found in admin registry after registration!")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register User: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering Role model...")
try:
    admin.site.register(Role)
    print(f"DEBUG: Role registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Role: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering Course model...")
try:
    admin.site.register(Course)
    print(f"DEBUG: Course registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Course: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering CourseThreshold model...")
try:
    admin.site.register(CourseThreshold)
    print(f"DEBUG: CourseThreshold registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register CourseThreshold: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering Exam model...")
try:
    admin.site.register(Exam)
    print(f"DEBUG: Exam registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Exam: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering LearningOutcome model...")
try:
    admin.site.register(LearningOutcome)
    print(f"DEBUG: LearningOutcome registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register LearningOutcome: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering ExamLOWeight model...")
try:
    admin.site.register(ExamLOWeight)
    print(f"DEBUG: ExamLOWeight registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register ExamLOWeight: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering Announcement model...")
try:
    admin.site.register(Announcement)
    print(f"DEBUG: Announcement registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register Announcement: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Registering ExamResult model...")
try:
    admin.site.register(ExamResult)
    print(f"DEBUG: ExamResult registered successfully")
except Exception as e:
    print(f"DEBUG ERROR: Failed to register ExamResult: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Final admin.site._registry =")
for model, admin_class in admin.site._registry.items():
    print(f"DEBUG:   - {model} -> {admin_class}")

# Additional verification
print("DEBUG: Verifying User model visibility...")
try:
    if User in admin.site._registry:
        user_admin = admin.site._registry[User]
        print(f"DEBUG: User model is registered with admin class: {user_admin}")
        print(f"DEBUG: User model verbose_name: {User._meta.verbose_name}")
        print(f"DEBUG: User model verbose_name_plural: {User._meta.verbose_name_plural}")
        print(f"DEBUG: User admin has_permission check: {hasattr(user_admin, 'has_view_permission')}")
    else:
        print(f"DEBUG: ✗ CRITICAL: User model NOT in admin registry!")
except Exception as e:
    print(f"DEBUG ERROR during verification: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
print("DEBUG: eys/admin.py loading complete")
print("=" * 80)
