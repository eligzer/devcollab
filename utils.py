from models import db, ActivityLog, User
from extensions import socketio
from datetime import datetime

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
    
    # Broadcast to all connected clients
    user = User.query.get(user_id)
    if user:
        activity_data = {
            'username': user.username,
            'profile_image': user.profile_image or 'default.jpg',
            'description': description,
            'created_at': datetime.now().strftime('%b %d, %Y %I:%M %p')
        }
        socketio.emit('new_activity', activity_data, broadcast=True)
