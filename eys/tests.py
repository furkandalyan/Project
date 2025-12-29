from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Role

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
