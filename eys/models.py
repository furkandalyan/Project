from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_given",
        limit_choices_to={'role__name__in': [
            'Regular Instructor',
            'Advisor Instructor',
            'Head of Department',
        ]}
    )

    students = models.ManyToManyField(
        User,
        blank=True,
        related_name="courses_taken",
        limit_choices_to={'role__name': 'Student'}
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    weight = models.FloatField()

    def __str__(self):
        return f"{self.course.code} - {self.name}"