from django.core.management.base import BaseCommand
from resumes.models import Resume, JobDescription, SimilarityScore
from matcher.utils import calculate_similarity

class Command(BaseCommand):
    help = 'Calculate similarity scores for all resumes and job descriptions'

    def handle(self, *args, **options):
        resumes = Resume.objects.filter(extracted_text__isnull=False)
        job_descriptions = JobDescription.objects.filter(extracted_text__isnull=False, is_active=True)
        
        self.stdout.write(f'Found {resumes.count()} resumes and {job_descriptions.count()} job descriptions')
        
        for resume in resumes:
            for jd in job_descriptions:
                score = calculate_similarity(resume.extracted_text, jd.extracted_text)
                SimilarityScore.objects.update_or_create(
                    resume=resume,
                    job_description=jd,
                    defaults={'score': score}
                )
                self.stdout.write(f'Calculated score {score:.2f} for Resume {resume.id} and JD {jd.id}')
        
        self.stdout.write(self.style.SUCCESS('Successfully calculated all similarity scores')) 