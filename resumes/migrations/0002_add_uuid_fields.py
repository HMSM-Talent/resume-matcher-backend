from django.db import migrations, models
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resume',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True),
        ),
    ] 