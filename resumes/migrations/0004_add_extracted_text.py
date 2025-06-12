from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0003_update_jobdescription_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='resume',
            name='extracted_text',
            field=models.TextField(blank=True, null=True),
        ),
    ] 