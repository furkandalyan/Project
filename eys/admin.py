from django.contrib import admin
from .models import Role, User,Course,Exam,LearningOutcome

admin.site.register(Role)
admin.site.register(User)
admin.site.register(Course)
admin.site.register(Exam)
admin.site.register(LearningOutcome)