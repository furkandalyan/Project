from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eys', '0003_user_advisor'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='advisor_note',
            field=models.TextField(blank=True, default=''),
        ),
    ]
