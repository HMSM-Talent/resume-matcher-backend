from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid
import resumes.models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Resume',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to=resumes.models.get_resume_upload_path)),
                ('original_filename', models.CharField(max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resumes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='JobDescription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('company_name', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('job_type', models.CharField(choices=[('FULL_TIME', 'Full Time'), ('PART_TIME', 'Part Time'), ('CONTRACT', 'Contract'), ('INTERNSHIP', 'Internship'), ('REMOTE', 'Remote')], max_length=50)),
                ('experience_level', models.CharField(choices=[('ENTRY', 'Entry Level'), ('MID', 'Mid Level'), ('SENIOR', 'Senior Level'), ('LEAD', 'Lead Level'), ('MANAGER', 'Manager Level')], max_length=50)),
                ('required_skills', models.TextField()),
                ('file', models.FileField(upload_to=resumes.models.get_jd_upload_path)),
                ('extracted_text', models.TextField(blank=True, null=True)),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('close_reason', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_descriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user', 'is_active'], name='resumes_job_user_id_f93758_idx'),
                    models.Index(fields=['created_at'], name='resumes_job_created_e395b6_idx'),
                    models.Index(fields=['title'], name='resumes_job_title_7ea4ac_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('company_feedback', models.TextField(blank=True, null=True)),
                ('similarity_score', models.FloatField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='resumes.jobdescription')),
                ('resume', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='resumes.resume')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['job', 'status'], name='resumes_job_job_id_eef83f_idx'),
                    models.Index(fields=['resume', 'status'], name='resumes_job_resume__2aaaae_idx'),
                    models.Index(fields=['created_at'], name='resumes_job_created_2aaaae_idx'),
                ],
            },
        ),
    ] 