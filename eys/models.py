print("=" * 80)
print("DEBUG: eys/models.py is being loaded")
print("=" * 80)

from django.db import models
print("DEBUG: django.db.models imported successfully")

from django.contrib.auth.models import AbstractUser
print("DEBUG: AbstractUser imported successfully")
print(f"DEBUG: AbstractUser = {AbstractUser}")


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

print("DEBUG: Role model class defined")
print(f"DEBUG: Role._meta = {Role._meta if hasattr(Role, '_meta') else 'Not yet initialized'}")


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    advisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advisees",
    )
    advisor_note = models.TextField(blank=True, default="")

    def save(self, *args, **kwargs):
        old_advisor_id = None
        if self.pk:
            old_advisor_id = User.objects.filter(pk=self.pk).values_list("advisor_id", flat=True).first()
        new_advisor_id = self.advisor_id
        super().save(*args, **kwargs)
        # Update advisor roles whenever advisor assignment changes or this is a student save.
        is_student = bool(self.role and self.role.name == "Student")
        if old_advisor_id != new_advisor_id or is_student:
            _update_advisor_role_by_id(old_advisor_id)
            _update_advisor_role_by_id(new_advisor_id)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username

print("DEBUG: User model class defined")
print(f"DEBUG: User.__bases__ = {User.__bases__}")
print(f"DEBUG: User._meta = {User._meta if hasattr(User, '_meta') else 'Not yet initialized'}")
print("=" * 80)
print("DEBUG: eys/models.py loading complete")
print("=" * 80)


def _update_advisor_role_by_id(advisor_id):
    if not advisor_id:
        return
    advisor = User.objects.filter(pk=advisor_id).select_related("role").first()
    if not advisor:
        return
    current_role = advisor.role.name if advisor.role else None
    if current_role == "Head of Department":
        return
    advisee_count = User.objects.filter(role__name="Student", advisor=advisor).count()
    if advisee_count > 0:
        target_role, _ = Role.objects.get_or_create(name="Advisor Instructor")
        if target_role and current_role != "Advisor Instructor":
            User.objects.filter(pk=advisor.id).update(role=target_role)
    else:
        target_role, _ = Role.objects.get_or_create(name="Regular Instructor")
        if target_role and current_role == "Advisor Instructor":
            User.objects.filter(pk=advisor.id).update(role=target_role)


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


class CourseThreshold(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="threshold")
    stable_min = models.DecimalField(max_digits=5, decimal_places=2, default=80)
    watch_min = models.DecimalField(max_digits=5, decimal_places=2, default=65)
    pass_min = models.DecimalField(max_digits=5, decimal_places=2, default=60)

    class Meta:
        verbose_name = "Course Threshold"
        verbose_name_plural = "Course Thresholds"

    def __str__(self):
        return f"{self.course.code} thresholds"

    def as_dict(self):
        return {
            "stable_min": float(self.stable_min),
            "watch_min": float(self.watch_min),
            "pass_min": float(self.pass_min),
        }


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


class ProgrammingOutcome(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class LOPOWeight(models.Model):
    learning_outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name="po_weights",
    )
    programming_outcome = models.ForeignKey(
        ProgrammingOutcome,
        on_delete=models.CASCADE,
        related_name="lo_weights",
    )
    weight = models.FloatField()  # LO -> PO aktarim yuzdesi

    class Meta:
        unique_together = ("learning_outcome", "programming_outcome")

    def __str__(self):
        return f"{self.learning_outcome} -> {self.programming_outcome} (%{self.weight})"


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
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-created_at"]

    def __str__(self):
        if self.course:
            return f"{self.course.code} - {self.title}"
        return self.title


class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f'Comment by {self.author} on {self.announcement}'


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    is_group = models.BooleanField(default=False)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    attachment = models.FileField(upload_to="assignments/", null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_created",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={'role__name': 'Student'},
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to="submissions/", null=True, blank=True)
    text = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions",
        limit_choices_to={'role__name__in': [
            'Regular Instructor',
            'Advisor Instructor',
            'Head of Department',
        ]},
    )
    group = models.ForeignKey("AssignmentGroup", on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")
    version = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student} - {self.assignment}"


class SubmissionAttachment(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="submission_attachments/")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attachment v{self.version} for {self.submission}"


class AssignmentCriterion(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="criteria")
    title = models.CharField(max_length=200)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.assignment} - {self.title}"


class SubmissionCriterionScore(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="criterion_scores")
    criterion = models.ForeignKey(AssignmentCriterion, on_delete=models.CASCADE, related_name="scores")
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ("submission", "criterion")

    def __str__(self):
        return f"{self.submission} - {self.criterion}"


class AssignmentGroup(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name="assignment_groups", blank=True)

    class Meta:
        unique_together = ("assignment", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.assignment} - {self.name}"


class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    week = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to="course_materials/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="materials_created"
    )

    class Meta:
        ordering = ["course_id", "week", "-created_at"]

    def __str__(self):
        return f"{self.course.code} - Hafta {self.week}: {self.title}"


class AssignmentTemplate(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    attachment = models.FileField(upload_to="assignment_templates/", null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignment_templates")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Notification(models.Model):
    KIND_CHOICES = [
        ("new_assignment", "New Assignment"),
        ("assignment_due", "Assignment Due Soon"),
        ("submission_received", "Submission Received"),
        ("submission_graded", "Submission Graded"),
        ("announcement_comment", "Announcement Comment"),
        ("exam_reminder", "Exam Reminder"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=50, choices=KIND_CHOICES)
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True, default="")
    payload = models.TextField(blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.kind}"
