from .models import UserHistory

def record_user_activity(user, action_type, description, company_name=None, job_title=None, job_description=None, status=UserHistory.Status.PENDING):
    """
    Record a user's activity in the history
    
    Args:
        user: The user performing the action
        action_type: Type of action (from UserHistory.ActionType)
        description: Description of the action
        company_name: Name of the company (optional)
        job_title: Title of the job (optional)
        job_description: Description of the job (optional)
        status: Status of the action (default: PENDING)
    """
    UserHistory.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        company_name=company_name,
        job_title=job_title,
        job_description=job_description,
        status=status
    ) 