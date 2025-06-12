from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0002_add_uuid_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobdescription',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ] 