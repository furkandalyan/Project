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
    description = models.TextField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.course.code} - {self.name}"


class LearningOutcome(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class ExamLOWeight(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE)
    weight = models.FloatField()  # Bu LO’ya etki yüzdesi (%30 gibi)

    def __str__(self):
        return f"{self.exam.name} → {self.learning_outcome.title} (%{self.weight})"


class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exam_results",
        limit_choices_to={'role__name': 'Student'}
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("exam", "student")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student} - {self.exam} ({self.score})"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True, related_name="announcements"
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="announcements"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-created_at"]

    def __str__(self):
        if self.course:
            return f"{self.course.code} - {self.title}"
        return self.title
