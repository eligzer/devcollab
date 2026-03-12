from models import db, ActivityLog


def log_activity(user_id, action_type, target_type, target_id, description):
    """Record a platform activity."""
    entry = ActivityLog(
        user_id=user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        description=description
    )
    db.session.add(entry)
