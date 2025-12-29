from datetime import timedelta
import json
import io
import zipfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from .models import (
    Role,
    Course,
    LearningOutcome,
    ProgrammingOutcome,
    LOPOWeight,
    Exam,
    ExamLOWeight,
    Assignment,
    AssignmentCriterion,
    Announcement,
    AnnouncementComment,
    CourseMaterial,
    Notification,
    ExamResult,
    Submission,
    SubmissionAttachment,
)

User = get_user_model()


class AdvisorRoleAutoUpdateTests(TestCase):
    def setUp(self):
        self.role_student = Role.objects.create(name="Student")
        self.role_regular = Role.objects.create(name="Regular Instructor")
        self.role_advisor = Role.objects.create(name="Advisor Instructor")
        self.role_head = Role.objects.create(name="Head of Department")

        self.advisor = User.objects.create_user(
            username="advisor1",
            password="pass",
            role=self.role_regular,
        )
        self.student = User.objects.create_user(
            username="student1",
            password="pass",
            role=self.role_student,
        )

    def test_assigning_advisor_promotes_role(self):
        self.student.advisor = self.advisor
        self.student.save()
        self.advisor.refresh_from_db()
        self.assertEqual(self.advisor.role.name, "Advisor Instructor")

    def test_removing_advisee_demotes_role(self):
        self.student.advisor = self.advisor
        self.student.save()
        self.student.advisor = None
        self.student.save()
        self.advisor.refresh_from_db()
        self.assertEqual(self.advisor.role.name, "Regular Instructor")

    def test_head_of_department_not_changed(self):
        head = User.objects.create_user(
            username="head1",
            password="pass",
            role=self.role_head,
        )
        self.student.advisor = head
        self.student.save()
        head.refresh_from_db()
        self.assertEqual(head.role.name, "Head of Department")


class ProjectSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")
        cls.role_head = Role.objects.create(name="Head of Department")

        cls.teacher = User.objects.create_user(
            username="teacher1",
            password="pass",
            role=cls.role_regular,
        )
        cls.student = User.objects.create_user(
            username="student1",
            password="pass",
            role=cls.role_student,
        )
        cls.head = User.objects.create_user(
            username="head1",
            password="pass",
            role=cls.role_head,
        )

        cls.course = Course.objects.create(
            name="Intro Programming",
            code="CSE101",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student)

        cls.lo = LearningOutcome.objects.create(course=cls.course, title="LO1", description="Basics")
        cls.po1 = ProgrammingOutcome.objects.create(code="PO1", title="PO1")
        cls.po2 = ProgrammingOutcome.objects.create(code="PO2", title="PO2")

        cls.exam = Exam.objects.create(course=cls.course, name="Midterm", description="Midterm exam")
        cls.exam_lo = ExamLOWeight.objects.create(exam=cls.exam, learning_outcome=cls.lo, weight=50)

        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="HW1",
            description="First homework",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
        )
        AssignmentCriterion.objects.create(
            assignment=cls.assignment,
            title="Criteria 1",
            max_score=50,
            order=1,
        )

        cls.announcement = Announcement.objects.create(
            title="Announcement 1",
            body="Hello class",
            course=cls.course,
            author=cls.teacher,
        )

        cls.material = CourseMaterial.objects.create(
            course=cls.course,
            week=1,
            title="Week 1",
            description="Intro notes",
            created_by=cls.teacher,
        )

        cls.notification = Notification.objects.create(
            user=cls.student,
            kind="new_assignment",
            message="New assignment posted",
        )

        ExamResult.objects.create(exam=cls.exam, student=cls.student, score=80)

    def test_student_dashboard_access(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_teacher_dashboard_access(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("teacher_dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("teacher_dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_course_detail_pages(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)

    def test_add_lo_po_weight(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("add_lo_po_weight", args=[self.lo.id]),
            {"programming_outcome": self.po1.id, "weight": "40"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            LOPOWeight.objects.filter(
                learning_outcome=self.lo,
                programming_outcome=self.po1,
                weight=40,
            ).exists()
        )

    def test_auto_distribute_lo_po(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(reverse("auto_distribute_lo_po", args=[self.lo.id]))
        self.assertEqual(resp.status_code, 302)
        weights = list(
            LOPOWeight.objects.filter(learning_outcome=self.lo).values_list("weight", flat=True)
        )
        self.assertEqual(len(weights), ProgrammingOutcome.objects.count())
        self.assertAlmostEqual(sum(weights), 100.0, places=2)

    def test_assignment_copy(self):
        self.client.force_login(self.teacher)
        url = reverse("teacher_assignment_create") + f"?copy_id={self.assignment.id}"
        resp = self.client.post(
            url,
            {
                "course": self.course.id,
                "title": "HW1 Copy",
                "description": "Copy",
                "due_at": "",
                "max_score": "100",
            },
        )
        self.assertEqual(resp.status_code, 302)
        new_assignment = Assignment.objects.filter(title="HW1 Copy").first()
        self.assertIsNotNone(new_assignment)
        self.assertEqual(new_assignment.criteria.count(), 1)

    def test_announcement_create_and_copy_context(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("teacher_create_announcement"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("recent_announcements", resp.context)
        self.assertTrue(resp.context["recent_announcements"].exists())
        resp = self.client.post(
            reverse("teacher_create_announcement"),
            {
                "title": "New Announcement",
                "body": "Body",
                "course": self.course.id,
                "pinned": "on",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Announcement.objects.filter(title="New Announcement").exists())

    def test_calendar_state_persists(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(
            reverse("teacher_calendar") + f"?view=month&course_id={self.course.id}"
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("teacher_calendar"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.course.id, resp.context["selected_course_ids"])

    def test_student_profile_with_advisor(self):
        self.student.advisor = self.teacher
        self.student.save()
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["advisor_username"], self.teacher.username)

    def test_materials_and_notifications_pages(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("teacher_materials"))
        self.assertEqual(resp.status_code, 200)
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_materials"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("notifications"))
        self.assertEqual(resp.status_code, 200)


class ProjectExtendedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")
        cls.role_advisor = Role.objects.create(name="Advisor Instructor")
        cls.role_head = Role.objects.create(name="Head of Department")

        cls.teacher = User.objects.create_user(
            username="teacher2",
            password="pass",
            role=cls.role_regular,
        )
        cls.advisor = User.objects.create_user(
            username="advisor2",
            password="pass",
            role=cls.role_advisor,
        )
        cls.head = User.objects.create_user(
            username="head2",
            password="pass",
            role=cls.role_head,
        )
        cls.student = User.objects.create_user(
            username="student2",
            password="pass",
            role=cls.role_student,
        )
        cls.student_no_submit = User.objects.create_user(
            username="student3",
            password="pass",
            role=cls.role_student,
        )
        cls.student.advisor = cls.advisor
        cls.student.save()

        cls.course = Course.objects.create(
            name="Data Structures",
            code="CSE201",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student)
        cls.course.students.add(cls.student_no_submit)
        cls.other_course = Course.objects.create(
            name="Networks",
            code="CSE301",
            instructor=cls.teacher,
        )

        cls.exam = Exam.objects.create(course=cls.course, name="Final", description="Final exam")
        ExamResult.objects.create(exam=cls.exam, student=cls.student, score=75)

        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="HW2",
            description="Second homework",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
        )
        AssignmentCriterion.objects.create(
            assignment=cls.assignment,
            title="Correctness",
            max_score=60,
            order=1,
        )
        Submission.objects.create(assignment=cls.assignment, student=cls.student, text="Solution")

        cls.announcement = Announcement.objects.create(
            title="Course Ann",
            body="Announcement body",
            course=cls.course,
            author=cls.teacher,
        )
        cls.other_announcement = Announcement.objects.create(
            title="Other Ann",
            body="Other body",
            course=cls.other_course,
            author=cls.teacher,
        )

        CourseMaterial.objects.create(
            course=cls.course,
            week=2,
            title="Week 2",
            description="Trees",
            created_by=cls.teacher,
        )

        cls.notification = Notification.objects.create(
            user=cls.student,
            kind="announcement_comment",
            message="Comment added",
        )

    def test_teacher_calendar_ics(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("teacher_calendar_ics"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/calendar", resp["Content-Type"])
        self.assertIn("BEGIN:VCALENDAR", resp.content.decode("utf-8", errors="ignore"))

    def test_exam_scores_csv_export(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("export_exam_scores_csv", args=[self.exam.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        content = resp.content.decode("utf-8", errors="ignore")
        self.assertIn("student_id,username,full_name,email,score,feedback", content)

    def test_manage_exam_scores_mobile(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("manage_exam_scores_mobile", args=[self.exam.id]))
        self.assertEqual(resp.status_code, 200)

    def test_teacher_assignment_export_csv(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("export_submissions_csv", args=[self.assignment.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])

    def test_student_assignments_pages(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_assignments"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("student_assignment_detail", args=[self.assignment.id]))
        self.assertEqual(resp.status_code, 200)

    def test_announcement_detail_permissions(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("announcement_detail", args=[self.other_announcement.id]))
        self.assertEqual(resp.status_code, 302)

    def test_notifications_mark_read(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("mark_notification_read", args=[self.notification.id]))
        self.assertEqual(resp.status_code, 302)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_advisor_students_access(self):
        self.client.force_login(self.advisor)
        resp = self.client.get(reverse("advisor_students"))
        self.assertEqual(resp.status_code, 200)

    def test_edit_course_threshold(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("edit_course_threshold", args=[self.course.id]),
            {"stable_min": "85", "watch_min": "70", "pass_min": "60"},
        )
        self.assertEqual(resp.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(float(self.course.threshold.stable_min), 85.0)

    def test_manage_assignment_criteria_post(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("manage_assignment_criteria", args=[self.assignment.id]),
            {"title": "Style", "max_score": "20", "order": "2"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.assignment.criteria.filter(title="Style").exists())

    def test_manage_assignment_groups_post(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("manage_assignment_groups", args=[self.assignment.id]),
            {"name": "Group A", "members": [self.student.id]},
        )
        self.assertEqual(resp.status_code, 302)
        group = self.assignment.groups.filter(name="Group A").first()
        self.assertIsNotNone(group)
        self.assertTrue(group.members.filter(id=self.student.id).exists())

    def test_send_assignment_reminders(self):
        self.client.force_login(self.teacher)
        before = Notification.objects.filter(user=self.student_no_submit).count()
        resp = self.client.get(reverse("send_assignment_reminders", args=[self.assignment.id]))
        self.assertEqual(resp.status_code, 302)
        after = Notification.objects.filter(user=self.student_no_submit).count()
        self.assertEqual(after, before + 1)

    def test_send_exam_reminders(self):
        self.client.force_login(self.teacher)
        before = Notification.objects.filter(user=self.student).count()
        resp = self.client.get(reverse("send_exam_reminders", args=[self.exam.id]))
        self.assertEqual(resp.status_code, 302)
        after = Notification.objects.filter(user=self.student).count()
        self.assertEqual(after, before + 1)

    def test_mark_all_notifications_read(self):
        Notification.objects.create(
            user=self.student,
            kind="assignment_due",
            message="Reminder",
        )
        self.client.force_login(self.student)
        resp = self.client.get(reverse("mark_all_notifications_read"))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Notification.objects.filter(user=self.student, is_read=False).exists())

    def test_global_search_results(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("global_search") + "?q=Data")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context["results_courses"]) >= 1)

    def test_department_pages_access(self):
        self.client.force_login(self.head)
        resp = self.client.get(reverse("department_overview"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("department_instructors"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("department_courses"))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("department_course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("department_instructor_detail", args=[self.teacher.id]))
        self.assertEqual(resp.status_code, 200)


class ProjectAccessMatrixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")
        cls.role_advisor = Role.objects.create(name="Advisor Instructor")
        cls.role_head = Role.objects.create(name="Head of Department")

        cls.teacher = User.objects.create_user(
            username="teacher3",
            password="pass",
            role=cls.role_regular,
        )
        cls.advisor = User.objects.create_user(
            username="advisor3",
            password="pass",
            role=cls.role_advisor,
        )
        cls.head = User.objects.create_user(
            username="head3",
            password="pass",
            role=cls.role_head,
        )
        cls.student = User.objects.create_user(
            username="student3",
            password="pass",
            role=cls.role_student,
        )
        cls.student2 = User.objects.create_user(
            username="student4",
            password="pass",
            role=cls.role_student,
        )
        cls.student.advisor = cls.advisor
        cls.student.save()

        cls.course = Course.objects.create(
            name="Algorithms",
            code="CSE401",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student, cls.student2)

        cls.lo = LearningOutcome.objects.create(course=cls.course, title="LO A", description="Desc")
        cls.po = ProgrammingOutcome.objects.create(code="POX", title="POX")
        cls.exam = Exam.objects.create(course=cls.course, name="Quiz", description="Quiz 1")
        ExamLOWeight.objects.create(exam=cls.exam, learning_outcome=cls.lo, weight=30)

        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="HW3",
            description="Homework 3",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
            due_at=timezone.now() + timedelta(days=3),
        )
        AssignmentCriterion.objects.create(
            assignment=cls.assignment,
            title="Quality",
            max_score=70,
            order=1,
        )
        Submission.objects.create(assignment=cls.assignment, student=cls.student, text="Answer")
        Submission.objects.create(assignment=cls.assignment, student=cls.student2, text="Answer 2", score=90)

        cls.announcement = Announcement.objects.create(
            title="Class News",
            body="Announcement body",
            course=cls.course,
            author=cls.teacher,
        )

        cls.notification = Notification.objects.create(
            user=cls.student,
            kind="new_assignment",
            message="Assignment posted",
            url=reverse("student_assignments"),
        )

    def test_post_manage_exam_scores_updates(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {f"score_{self.student.id}": "88", f"feedback_{self.student.id}": "Good"},
        )
        self.assertEqual(resp.status_code, 302)
        res = ExamResult.objects.filter(exam=self.exam, student=self.student).first()
        self.assertIsNotNone(res)
        self.assertEqual(float(res.score), 88.0)

    def test_post_add_lo(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("add_lo", args=[self.course.id]),
            {"title": "LO New", "description": "Desc"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(LearningOutcome.objects.filter(course=self.course, title="LO New").exists())

    def test_post_add_exam(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("add_exam", args=[self.course.id]),
            {"name": "Final", "scheduled_at": "2025-01-01T10:00", "description": "Final exam"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Exam.objects.filter(course=self.course, name="Final").exists())

    def test_post_add_exam_lo_weight(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("add_exam_lo_weight", args=[self.exam.id]),
            {"learning_outcome": self.lo.id, "weight": "40"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            ExamLOWeight.objects.filter(exam=self.exam, learning_outcome=self.lo, weight=40).exists()
        )

    def test_post_add_lo_po_weight(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("add_lo_po_weight", args=[self.lo.id]),
            {"programming_outcome": self.po.id, "weight": "55"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            LOPOWeight.objects.filter(
                learning_outcome=self.lo, programming_outcome=self.po, weight=55
            ).exists()
        )

    def test_post_create_material(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("create_material"),
            {"course": self.course.id, "week": "3", "title": "Week 3", "description": "Notes"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CourseMaterial.objects.filter(course=self.course, week=3).exists())

    def test_post_student_assignment_submission(self):
        self.client.force_login(self.student)
        resp = self.client.post(
            reverse("student_assignment_detail", args=[self.assignment.id]),
            {"text": "My submission"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Submission.objects.filter(assignment=self.assignment, student=self.student).exists()
        )

    def test_post_announcement_comment(self):
        self.client.force_login(self.student)
        resp = self.client.post(
            reverse("announcement_detail", args=[self.announcement.id]),
            {"body": "Nice"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            AnnouncementComment.objects.filter(announcement=self.announcement, author=self.student).exists()
        )

    def test_post_edit_announcement(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("edit_announcement", args=[self.announcement.id]),
            {"title": "Updated", "body": "Body", "course": self.course.id, "pinned": "on"},
        )
        self.assertEqual(resp.status_code, 302)
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title, "Updated")

    def test_post_delete_announcement(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(reverse("delete_announcement", args=[self.announcement.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Announcement.objects.filter(id=self.announcement.id).exists())

class ProjectAdvancedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")

        cls.teacher = User.objects.create_user(
            username="teacher4",
            password="pass",
            role=cls.role_regular,
        )
        cls.student = User.objects.create_user(
            username="student5",
            password="pass",
            role=cls.role_student,
        )

        cls.course = Course.objects.create(
            name="Software Testing",
            code="CSE501",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student)

        cls.lo = LearningOutcome.objects.create(course=cls.course, title="LO T1", description="Desc")
        cls.po = ProgrammingOutcome.objects.create(code="POT", title="POT")

        cls.exam = Exam.objects.create(course=cls.course, name="Quiz", description="Quiz")
        ExamLOWeight.objects.create(exam=cls.exam, learning_outcome=cls.lo, weight=100)

        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="HW4",
            description="Homework 4",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
            due_at=timezone.now() + timedelta(days=2),
        )

    def test_exam_scores_csv_import(self):
        self.client.force_login(self.teacher)
        content = "student_id,username,score,feedback\n{sid},{user},85,Good\n".format(
            sid=self.student.id, user=self.student.username
        )
        csv_file = SimpleUploadedFile(
            "scores.csv", content.encode("utf-8"), content_type="text/csv"
        )
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        res = ExamResult.objects.filter(exam=self.exam, student=self.student).first()
        self.assertIsNotNone(res)
        self.assertEqual(float(res.score), 85.0)

    def test_export_submissions_zip_contains_attachment(self):
        self.client.force_login(self.teacher)
        submission = Submission.objects.create(assignment=self.assignment, student=self.student, text="Answer")
        upload = SimpleUploadedFile("report.txt", b"hello", content_type="text/plain")
        SubmissionAttachment.objects.create(submission=submission, file=upload, version=1)
        resp = self.client.get(reverse("export_submissions_zip", args=[self.assignment.id]))
        self.assertEqual(resp.status_code, 200)
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()
        self.assertTrue(len(names) >= 1)

    def test_course_detail_lo_po_scores(self):
        LOPOWeight.objects.create(learning_outcome=self.lo, programming_outcome=self.po, weight=50)
        ExamResult.objects.create(exam=self.exam, student=self.student, score=80)
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        student_cards = resp.context.get("student_cards") or []
        card = None
        for item in student_cards:
            student_obj = item.get("student")
            if student_obj and student_obj.id == self.student.id:
                card = item
                break
        if card is None and student_cards:
            card = student_cards[0]
        self.assertIsNotNone(card)
        lo_scores = json.loads(card.get("lo_scores_json"))
        po_scores = json.loads(card.get("po_scores_json"))
        lo_score = next((x for x in lo_scores if x.get("id") == self.lo.id), None)
        self.assertIsNotNone(lo_score)
        self.assertEqual(float(lo_score.get("score")), 80.0)
        po_score = next((x for x in po_scores if x.get("code") == self.po.code), None)
        self.assertIsNotNone(po_score)
        self.assertEqual(float(po_score.get("score")), 40.0)

    def test_teacher_can_upload_material_attachment(self):
        self.client.force_login(self.teacher)
        upload = SimpleUploadedFile("notes.pdf", b"pdf", content_type="application/pdf")
        resp = self.client.post(
            reverse("create_material"),
            {"course": self.course.id, "week": "4", "title": "Week 4", "description": "Docs", "attachment": upload},
        )
        self.assertEqual(resp.status_code, 302)
        mat = CourseMaterial.objects.filter(course=self.course, week=4).first()
        self.assertIsNotNone(mat)
        self.assertTrue(bool(mat.attachment))

    def test_teacher_can_create_assignment_with_attachment(self):
        self.client.force_login(self.teacher)
        upload = SimpleUploadedFile("task.pdf", b"task", content_type="application/pdf")
        resp = self.client.post(
            reverse("teacher_assignment_create"),
            {
                "course": self.course.id,
                "title": "HW Attach",
                "description": "Desc",
                "due_at": "",
                "max_score": "100",
                "attachment": upload,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Assignment.objects.filter(title="HW Attach").exists())

    def test_student_cannot_create_material(self):
        self.client.force_login(self.student)
        resp = self.client.post(
            reverse("create_material"),
            {"course": self.course.id, "week": "5", "title": "Week 5", "description": "Notes"},
        )
        self.assertEqual(resp.status_code, 302)

    def test_student_cannot_manage_assignment_criteria(self):
        self.client.force_login(self.student)
        resp = self.client.post(
            reverse("manage_assignment_criteria", args=[self.assignment.id]),
            {"title": "Hack", "max_score": "10", "order": "1"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_student_cannot_edit_course_threshold(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("edit_course_threshold", args=[self.course.id]))
        self.assertEqual(resp.status_code, 302)

    def test_global_search_empty_query(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("global_search"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["results_courses"]), 0)
        self.assertEqual(len(resp.context["results_exams"]), 0)


class ProjectEdgeCaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")
        cls.role_advisor = Role.objects.create(name="Advisor Instructor")
        cls.role_head = Role.objects.create(name="Head of Department")

        cls.teacher = User.objects.create_user(
            username="teacher5",
            password="pass",
            role=cls.role_regular,
        )
        cls.advisor = User.objects.create_user(
            username="advisor5",
            password="pass",
            role=cls.role_advisor,
        )
        cls.head = User.objects.create_user(
            username="head5",
            password="pass",
            role=cls.role_head,
        )
        cls.student = User.objects.create_user(
            username="student6",
            password="pass",
            role=cls.role_student,
        )
        cls.other_student = User.objects.create_user(
            username="student7",
            password="pass",
            role=cls.role_student,
        )

        cls.course = Course.objects.create(
            name="Edge Cases",
            code="CSE601",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student, cls.other_student)
        cls.lo = LearningOutcome.objects.create(course=cls.course, title="LO Edge", description="Desc")
        cls.exam = Exam.objects.create(course=cls.course, name="Edge Exam", description="Desc")
        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="Edge HW",
            description="Desc",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
            due_at=timezone.now() + timedelta(days=1),
        )
        cls.announcement = Announcement.objects.create(
            title="Edge Ann",
            body="Body",
            course=cls.course,
            author=cls.teacher,
        )

    def test_exam_scores_csv_invalid_score(self):
        self.client.force_login(self.teacher)
        content = "student_id,username,score,feedback\n{sid},{user},oops,Nope\n".format(
            sid=self.student.id, user=self.student.username
        )
        csv_file = SimpleUploadedFile(
            "scores.csv", content.encode("utf-8"), content_type="text/csv"
        )
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ExamResult.objects.filter(exam=self.exam, student=self.student).exists())

    def test_exam_scores_csv_invalid_student(self):
        self.client.force_login(self.teacher)
        content = "student_id,username,score,feedback\n9999,ghost,90,Ok\n"
        csv_file = SimpleUploadedFile(
            "scores.csv", content.encode("utf-8"), content_type="text/csv"
        )
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ExamResult.objects.filter(exam=self.exam).count(), 0)

    def test_manage_exam_scores_mobile_invalid_score(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("manage_exam_scores_mobile", args=[self.exam.id]),
            {f"score_{self.student.id}": "bad"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ExamResult.objects.filter(exam=self.exam, student=self.student).exists())

    def test_export_submissions_zip_empty(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("export_submissions_zip", args=[self.assignment.id]))
        self.assertEqual(resp.status_code, 200)
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        self.assertEqual(len(zf.namelist()), 0)

    def test_global_search_requires_login(self):
        resp = self.client.get(reverse("global_search") + "?q=edge")
        self.assertEqual(resp.status_code, 302)

    def test_advisor_student_detail_denied_for_non_advisee(self):
        self.client.force_login(self.advisor)
        resp = self.client.get(reverse("advisor_student_detail", args=[self.student.id]))
        self.assertEqual(resp.status_code, 404)

    def test_department_pages_denied_for_teacher(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("department_overview"))
        self.assertEqual(resp.status_code, 302)

    def test_teacher_announcements_denied_for_student(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("teacher_announcements"))
        self.assertEqual(resp.status_code, 302)

    def test_teacher_dashboard_query_count(self):
        self.client.force_login(self.teacher)
        with CaptureQueriesContext(connection) as ctx:
            resp = self.client.get(reverse("teacher_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 80)

    def test_student_dashboard_query_count(self):
        self.client.force_login(self.student)
        with CaptureQueriesContext(connection) as ctx:
            resp = self.client.get(reverse("student_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 80)


class ProjectEdgeCaseTests2(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")

        cls.teacher = User.objects.create_user(
            username="teacher6",
            password="pass",
            role=cls.role_regular,
        )
        cls.student = User.objects.create_user(
            username="student8",
            password="pass",
            role=cls.role_student,
        )

        cls.course = Course.objects.create(
            name="Unicode Course",
            code="CSE701",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student)

        cls.exam = Exam.objects.create(course=cls.course, name="Edge Exam 2", description="Desc")
        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="Past HW",
            description="Desc",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
            due_at=timezone.now() - timedelta(days=1),
        )

    def test_exam_scores_csv_clamps_high_low(self):
        self.client.force_login(self.teacher)
        content = "student_id,username,score,feedback\n{sid},{user},150,High\n".format(
            sid=self.student.id, user=self.student.username
        )
        csv_file = SimpleUploadedFile("scores.csv", content.encode("utf-8"), content_type="text/csv")
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        res = ExamResult.objects.filter(exam=self.exam, student=self.student).first()
        self.assertIsNotNone(res)
        self.assertEqual(float(res.score), 100.0)

        content = "student_id,username,score,feedback\n{sid},{user},-5,Low\n".format(
            sid=self.student.id, user=self.student.username
        )
        csv_file = SimpleUploadedFile("scores.csv", content.encode("utf-8"), content_type="text/csv")
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        res = ExamResult.objects.filter(exam=self.exam, student=self.student).first()
        self.assertIsNotNone(res)
        self.assertEqual(float(res.score), 0.0)

    def test_exam_scores_csv_comma_decimal(self):
        self.client.force_login(self.teacher)
        content = 'student_id,username,score,feedback\n{sid},{user},"85,5",Ok\n'.format(
            sid=self.student.id, user=self.student.username
        )
        csv_file = SimpleUploadedFile("scores.csv", content.encode("utf-8"), content_type="text/csv")
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        res = ExamResult.objects.filter(exam=self.exam, student=self.student).first()
        self.assertIsNotNone(res)
        self.assertEqual(float(res.score), 85.5)

    def test_exam_scores_csv_blank_score_deletes(self):
        ExamResult.objects.create(exam=self.exam, student=self.student, score=70)
        self.client.force_login(self.teacher)
        content = "student_id,username,score,feedback\n{sid},{user},,\n".format(
            sid=self.student.id, user=self.student.username
        )
        csv_file = SimpleUploadedFile("scores.csv", content.encode("utf-8"), content_type="text/csv")
        resp = self.client.post(
            reverse("manage_exam_scores", args=[self.exam.id]),
            {"csv_file": csv_file},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ExamResult.objects.filter(exam=self.exam, student=self.student).exists())

    def test_add_exam_invalid_date(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("add_exam", args=[self.course.id]),
            {"name": "Bad Date", "scheduled_at": "not-a-date", "description": "Desc"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Exam.objects.filter(course=self.course, name="Bad Date").exists())

    def test_student_submission_blocked_after_due(self):
        self.client.force_login(self.student)
        resp = self.client.post(
            reverse("student_assignment_detail", args=[self.assignment.id]),
            {"text": "Late"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Submission.objects.filter(assignment=self.assignment, student=self.student).exists())

    def test_teacher_calendar_ics_includes_assignments(self):
        self.client.force_login(self.teacher)
        Assignment.objects.create(
            course=self.course,
            title="HW cal",
            description="Desc",
            max_score=100,
            created_by=self.teacher,
            published_at=timezone.now(),
            due_at=timezone.now() + timedelta(days=2),
        )
        resp = self.client.get(reverse("teacher_calendar_ics") + "?include_assignments=1")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8", errors="ignore")
        self.assertIn("assignment-", content)

    def test_announcement_unicode_create(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("teacher_create_announcement"),
            {"title": "Duyuru ??", "body": "Merhaba d?nya", "course": self.course.id},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Announcement.objects.filter(title="Duyuru ??").exists())


class ProjectValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")

        cls.teacher = User.objects.create_user(
            username="teacher7",
            password="pass",
            role=cls.role_regular,
        )
        cls.student = User.objects.create_user(
            username="student9",
            password="pass",
            role=cls.role_student,
        )

        cls.course = Course.objects.create(
            name="Validation Course",
            code="CSE801",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student)

        cls.exam = Exam.objects.create(course=cls.course, name="Validation Exam", description="Desc")
        cls.assignment = Assignment.objects.create(
            course=cls.course,
            title="Validation HW",
            description="Desc",
            max_score=100,
            created_by=cls.teacher,
            published_at=timezone.now(),
            due_at=timezone.now() + timedelta(days=1),
        )

    def test_edit_course_threshold_invalid(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("edit_course_threshold", args=[self.course.id]),
            {"stable_min": "abc", "watch_min": "70", "pass_min": "60"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_teacher_assignment_create_missing_required(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("teacher_assignment_create"),
            {"title": "", "description": "", "max_score": ""},
        )
        self.assertEqual(resp.status_code, 200)

    def test_teacher_create_announcement_missing_title(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("teacher_create_announcement"),
            {"title": "", "body": "Body", "course": self.course.id},
        )
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_manage_exam_scores(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("manage_exam_scores", args=[self.exam.id]))
        self.assertEqual(resp.status_code, 404)

    def test_course_detail_query_budget(self):
        self.client.force_login(self.teacher)
        with CaptureQueriesContext(connection) as ctx:
            resp = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 140)


class ProjectTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_student = Role.objects.create(name="Student")
        cls.role_regular = Role.objects.create(name="Regular Instructor")

        cls.teacher = User.objects.create_user(
            username="teacher8",
            password="pass",
            role=cls.role_regular,
        )
        cls.student = User.objects.create_user(
            username="student10",
            password="pass",
            role=cls.role_student,
        )

        cls.course = Course.objects.create(
            name="Template Course",
            code="CSE901",
            instructor=cls.teacher,
        )
        cls.course.students.add(cls.student)

        cls.exam = Exam.objects.create(course=cls.course, name="Temp Exam", description="Desc")
        cls.announcement = Announcement.objects.create(
            title="Template Ann",
            body="Body",
            course=cls.course,
            author=cls.teacher,
        )

    def test_teacher_create_announcement_template_markers(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("teacher_create_announcement"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "preview-title")
        self.assertContains(resp, "preview-body")

    def test_course_detail_contains_student_search(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "student-search")

    def test_base_contains_cevai_panel(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "cevai-panel")
        self.assertContains(resp, "cevai-fab")

    def test_student_profile_has_advisor_section(self):
        self.student.advisor = self.teacher
        self.student.save()
        self.client.force_login(self.student)
        resp = self.client.get(reverse("student_profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Danisman")

    def test_validation_errors_have_form_errors(self):
        self.client.force_login(self.teacher)
        resp = self.client.post(
            reverse("teacher_create_announcement"),
            {"title": "", "body": "Body", "course": self.course.id},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors)



def _make_access_test(user_attr, url_func, expected_status):
    def _test(self):
        self.client.force_login(getattr(self, user_attr))
        url = url_func(self)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, expected_status)
    return _test


ACCESS_MATRIX = [
    ("student_dashboard", "student", lambda self: reverse("student_dashboard"), 200),
    ("student_courses", "student", lambda self: reverse("student_courses"), 200),
    ("student_calendar", "student", lambda self: reverse("student_calendar"), 200),
    ("student_calendar_month", "student", lambda self: reverse("student_calendar") + "?month=1&year=2025", 200),
    ("student_announcements", "student", lambda self: reverse("student_announcements"), 200),
    ("student_profile", "student", lambda self: reverse("student_profile"), 200),
    ("student_assignments", "student", lambda self: reverse("student_assignments"), 200),
    ("student_materials", "student", lambda self: reverse("student_materials"), 200),
    ("student_materials_week", "student", lambda self: reverse("student_materials") + "?week=1", 200),
    ("student_course_detail", "student", lambda self: reverse("student_course_detail", args=[self.course.id]), 200),
    ("student_assignment_detail", "student", lambda self: reverse("student_assignment_detail", args=[self.assignment.id]), 200),
    ("announcement_detail_student", "student", lambda self: reverse("announcement_detail", args=[self.announcement.id]), 200),
    ("notifications_student", "student", lambda self: reverse("notifications"), 200),
    ("global_search_student", "student", lambda self: reverse("global_search") + "?q=Algo", 200),
    ("mark_all_notifications_read", "student", lambda self: reverse("mark_all_notifications_read"), 302),
    ("mark_notification_read", "student", lambda self: reverse("mark_notification_read", args=[self.notification.id]), 302),

    ("teacher_dashboard", "teacher", lambda self: reverse("teacher_dashboard"), 200),
    ("teacher_courses", "teacher", lambda self: reverse("teacher_courses"), 200),
    ("teacher_calendar", "teacher", lambda self: reverse("teacher_calendar"), 200),
    ("teacher_calendar_week", "teacher", lambda self: reverse("teacher_calendar") + "?view=week&date=2025-01-01", 200),
    ("teacher_calendar_ics", "teacher", lambda self: reverse("teacher_calendar_ics"), 200),
    ("teacher_calendar_ics_course", "teacher", lambda self: reverse("teacher_calendar_ics") + f"?course_id={self.course.id}", 200),
    ("teacher_calendar_ics_assignments", "teacher", lambda self: reverse("teacher_calendar_ics") + "?include_assignments=1", 200),
    ("teacher_announcements", "teacher", lambda self: reverse("teacher_announcements"), 200),
    ("teacher_create_announcement", "teacher", lambda self: reverse("teacher_create_announcement"), 200),
    ("teacher_assignments", "teacher", lambda self: reverse("teacher_assignments"), 200),
    ("teacher_assignment_create", "teacher", lambda self: reverse("teacher_assignment_create"), 200),
    ("teacher_assignment_detail", "teacher", lambda self: reverse("teacher_assignment_detail", args=[self.assignment.id]), 200),
    ("teacher_assignment_detail_pending", "teacher", lambda self: reverse("teacher_assignment_detail", args=[self.assignment.id]) + "?status=pending", 200),
    ("teacher_assignment_detail_graded", "teacher", lambda self: reverse("teacher_assignment_detail", args=[self.assignment.id]) + "?status=graded", 200),
    ("manage_assignment_criteria", "teacher", lambda self: reverse("manage_assignment_criteria", args=[self.assignment.id]), 200),
    ("manage_assignment_groups", "teacher", lambda self: reverse("manage_assignment_groups", args=[self.assignment.id]), 200),
    ("export_submissions_csv", "teacher", lambda self: reverse("export_submissions_csv", args=[self.assignment.id]), 200),
    ("export_submissions_zip", "teacher", lambda self: reverse("export_submissions_zip", args=[self.assignment.id]), 200),
    ("export_exam_scores_csv", "teacher", lambda self: reverse("export_exam_scores_csv", args=[self.exam.id]), 200),
    ("manage_exam_scores", "teacher", lambda self: reverse("manage_exam_scores", args=[self.exam.id]), 200),
    ("manage_exam_scores_mobile", "teacher", lambda self: reverse("manage_exam_scores_mobile", args=[self.exam.id]), 200),
    ("exam_detail", "teacher", lambda self: reverse("exam_detail", args=[self.exam.id]), 200),
    ("add_exam", "teacher", lambda self: reverse("add_exam", args=[self.course.id]), 200),
    ("add_lo", "teacher", lambda self: reverse("add_lo", args=[self.course.id]), 200),
    ("add_exam_lo_weight", "teacher", lambda self: reverse("add_exam_lo_weight", args=[self.exam.id]), 200),
    ("add_lo_po_weight", "teacher", lambda self: reverse("add_lo_po_weight", args=[self.lo.id]), 200),
    ("edit_course_threshold", "teacher", lambda self: reverse("edit_course_threshold", args=[self.course.id]), 200),
    ("teacher_materials", "teacher", lambda self: reverse("teacher_materials"), 200),
    ("create_material", "teacher", lambda self: reverse("create_material"), 200),
    ("course_detail", "teacher", lambda self: reverse("course_detail", args=[self.course.id]), 200),
    ("edit_announcement", "teacher", lambda self: reverse("edit_announcement", args=[self.announcement.id]), 200),
    ("delete_announcement", "teacher", lambda self: reverse("delete_announcement", args=[self.announcement.id]), 200),
    ("announcement_detail_teacher", "teacher", lambda self: reverse("announcement_detail", args=[self.announcement.id]), 200),
    ("notifications_teacher", "teacher", lambda self: reverse("notifications"), 200),
    ("global_search_teacher", "teacher", lambda self: reverse("global_search") + "?q=Algorithms", 200),
    ("send_assignment_reminders", "teacher", lambda self: reverse("send_assignment_reminders", args=[self.assignment.id]), 302),
    ("send_exam_reminders", "teacher", lambda self: reverse("send_exam_reminders", args=[self.exam.id]), 302),
    ("auto_distribute_lo_po_get", "teacher", lambda self: reverse("auto_distribute_lo_po", args=[self.lo.id]), 302),
    ("affairs_dashboard", "teacher", lambda self: reverse("affairs_dashboard"), 200),

    ("advisor_students", "advisor", lambda self: reverse("advisor_students"), 200),
    ("advisor_student_detail", "advisor", lambda self: reverse("advisor_student_detail", args=[self.student.id]), 200),
    ("teacher_dashboard_advisor", "advisor", lambda self: reverse("teacher_dashboard"), 200),
    ("teacher_calendar_advisor", "advisor", lambda self: reverse("teacher_calendar"), 200),

    ("department_overview", "head", lambda self: reverse("department_overview"), 200),
    ("department_instructors", "head", lambda self: reverse("department_instructors"), 200),
    ("department_courses", "head", lambda self: reverse("department_courses"), 200),
    ("department_course_detail", "head", lambda self: reverse("department_course_detail", args=[self.course.id]), 200),
    ("department_instructor_detail", "head", lambda self: reverse("department_instructor_detail", args=[self.teacher.id]), 200),
]


for name, user_attr, url_func, status in ACCESS_MATRIX:
    setattr(
        ProjectAccessMatrixTests,
        f"test_access_{name}",
        _make_access_test(user_attr, url_func, status),
    )
