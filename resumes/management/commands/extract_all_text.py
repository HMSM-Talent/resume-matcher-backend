from django.core.management.base import BaseCommand
from resumes.models import Resume, JobDescription
from matcher.utils import extract_pdf_text, extract_docx_text
import os

class Command(BaseCommand):
    help = 'Extract text from all existing resume and job description files'

    def handle(self, *args, **options):
        # Process Resumes
        resumes = Resume.objects.all()
        self.stdout.write(f'Processing {resumes.count()} resumes...')
        
        for resume in resumes:
            if not resume.extracted_text and resume.file:
                try:
                    file_path = resume.file.path
                    if file_path.lower().endswith('.pdf'):
                        text = extract_pdf_text(resume.file)
                    elif file_path.lower().endswith('.docx'):
                        text = extract_docx_text(resume.file)
                    else:
                        self.stdout.write(self.style.WARNING(f'Unsupported file type for resume {resume.id}: {file_path}'))
                        continue
                    
                    resume.extracted_text = text
                    resume.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully extracted text from resume {resume.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing resume {resume.id}: {str(e)}'))

        # Process Job Descriptions
        job_descriptions = JobDescription.objects.all()
        self.stdout.write(f'Processing {job_descriptions.count()} job descriptions...')
        
        for jd in job_descriptions:
            if not jd.extracted_text and jd.file:
                try:
                    file_path = jd.file.path
                    if file_path.lower().endswith('.pdf'):
                        text = extract_pdf_text(jd.file)
                    elif file_path.lower().endswith('.docx'):
                        text = extract_docx_text(jd.file)
                    else:
                        self.stdout.write(self.style.WARNING(f'Unsupported file type for job description {jd.id}: {file_path}'))
                        continue
                    
                    jd.extracted_text = text
                    jd.save()
                    self.stdout.write(self.style.SUCCESS(f'Successfully extracted text from job description {jd.id}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing job description {jd.id}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Text extraction completed!')) 