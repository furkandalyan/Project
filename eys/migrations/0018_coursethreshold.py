from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("eys", "0017_remove_assignmentgroup_assignment_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseThreshold",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stable_min", models.DecimalField(decimal_places=2, default=80, max_digits=5)),
                ("watch_min", models.DecimalField(decimal_places=2, default=65, max_digits=5)),
                ("pass_min", models.DecimalField(decimal_places=2, default=60, max_digits=5)),
                (
                    "course",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="threshold",
                        to="eys.course",
                    ),
                ),
            ],
            options={
                "verbose_name": "Course Threshold",
                "verbose_name_plural": "Course Thresholds",
            },
        ),
    ]
