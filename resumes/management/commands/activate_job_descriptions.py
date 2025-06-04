from django.core.management.base import BaseCommand
from resumes.models import JobDescription

class Command(BaseCommand):
    help = 'Activate all job descriptions'

    def handle(self, *args, **options):
        # Get all inactive job descriptions
        inactive_jds = JobDescription.objects.filter(is_active=False)
        count = inactive_jds.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No inactive job descriptions found'))
            return
            
        # Activate them
        inactive_jds.update(is_active=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully activated {count} job descriptions')
        ) 