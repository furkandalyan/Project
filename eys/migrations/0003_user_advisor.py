from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eys', '0002_alter_user_options_user_profile_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='advisor',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'role__name__in': ['Advisor Instructor', 'Head of Department']},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='advisees',
                to='eys.user',
            ),
        ),
    ]
