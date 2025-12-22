from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Role,
    User,
    Course,
    Exam,
    LearningOutcome,
    ExamLOWeight,
    Announcement,
    ExamResult,
    ProgramOutcome,
    LOPOWeight,
)

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


class LOPOWeightInline(admin.TabularInline):
    model = LOPOWeight
    extra = 1


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title", "description")
    inlines = [LOPOWeightInline]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)
admin.site.register(Course)
admin.site.register(Exam)
admin.site.register(LearningOutcome)
admin.site.register(ExamLOWeight)
admin.site.register(Announcement)
admin.site.register(ExamResult)
