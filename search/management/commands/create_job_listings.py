from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from search.models import JobListing
from resumes.models import JobDescription

class Command(BaseCommand):
    help = 'Creates JobListing entries for existing JobDescription objects that do not have them.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to create missing JobListing entries...'))

        job_descriptions = JobDescription.objects.all()
        created_count = 0

        with transaction.atomic():
            for jd in job_descriptions:
                # Check if a JobListing already exists for this JobDescription
                if not JobListing.objects.filter(job_description=jd).exists():
                    try:
                        # Create a new JobListing
                        JobListing.objects.create(
                            job_description=jd,
                            company=jd.user,  # Assuming the user who uploaded JD is the company
                            is_active=True
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully created JobListing for "{jd.title}" (ID: {jd.id})'
                            )
                        )
                        created_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error creating JobListing for "{jd.title}" (ID: {jd.id}): {e}'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'JobListing already exists for "{jd.title}" (ID: {jd.id}), skipping.'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Finished. Created {created_count} new JobListing entries.'
            )
        ) 