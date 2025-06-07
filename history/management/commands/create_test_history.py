from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from history.models import UserHistory
from history.utils import record_user_activity

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test history data for users'

    def handle(self, *args, **kwargs):
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))

        # Create sample history entries
        activities = [
            {
                'action_type': UserHistory.ActionType.RESUME_UPLOAD,
                'description': 'Uploaded resume for Software Engineer position',
                'status': UserHistory.Status.ACCEPTED
            },
            {
                'action_type': UserHistory.ActionType.JOB_APPLICATION,
                'description': 'Applied for Senior Developer position',
                'company_name': 'Tech Corp',
                'job_title': 'Senior Developer',
                'job_description': 'Looking for experienced developer',
                'status': UserHistory.Status.REVIEWING
            },
            {
                'action_type': UserHistory.ActionType.JOB_POST,
                'description': 'Posted new job opening',
                'company_name': 'Tech Corp',
                'job_title': 'Junior Developer',
                'job_description': 'Entry level position',
                'status': UserHistory.Status.PENDING
            },
            {
                'action_type': UserHistory.ActionType.PROFILE_UPDATE,
                'description': 'Updated profile information',
                'status': UserHistory.Status.ACCEPTED
            }
        ]

        for activity in activities:
            record_user_activity(user=user, **activity)

        self.stdout.write(self.style.SUCCESS('Successfully created test history data')) 