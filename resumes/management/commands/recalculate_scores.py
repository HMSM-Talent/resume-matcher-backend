from django.core.management.base import BaseCommand
from resumes.models import Resume, JobDescription
from matcher.models import SimilarityScore
from matcher.utils import calculate_similarity
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Recalculate similarity scores for a specific resume'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email of the candidate')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # Get the resume
            resume = Resume.objects.get(user__email=email)
            self.stdout.write(f"Found resume for {email}")
            
            # Get all active job descriptions
            job_descriptions = JobDescription.objects.filter(is_active=True)
            self.stdout.write(f"Found {job_descriptions.count()} active job descriptions")
            
            # Calculate scores
            for jd in job_descriptions:
                try:
                    score, _ = calculate_similarity(resume.extracted_text, jd.extracted_text)
                    SimilarityScore.objects.update_or_create(
                        resume=resume,
                        job_description=jd,
                        defaults={'score': score}
                    )
                    self.stdout.write(f"Calculated score {score:.2f} for JD {jd.id}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error calculating score for JD {jd.id}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully recalculated scores for {email}'))
            
        except Resume.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No resume found for {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 