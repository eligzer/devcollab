from models import db, Activity, User
from datetime import datetime

def log_activity(user_id, action, target_type, target_id, description):
    """Record a platform activity."""
    entry = Activity(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description
    )
    db.session.add(entry)
    db.session.commit()
