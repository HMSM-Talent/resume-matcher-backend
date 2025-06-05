from .history import UserHistory

def record_user_activity(user, action_type, description, ip_address=None, metadata=None):
    """
    Utility function to record user activities
    
    Args:
        user: The user performing the action
        action_type: One of UserHistory.ActionType choices
        description: Description of the activity
        ip_address: Optional IP address
        metadata: Optional dictionary of additional data
    """
    return UserHistory.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        ip_address=ip_address,
        metadata=metadata or {}
    ) 