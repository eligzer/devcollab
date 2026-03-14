def log_activity(user_id, action_type, target_type=None, target_id=None, description=None):

    from models import Activity
    from models import db

    try:

        activity = Activity(
            user_id=user_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            description=description
        )

        db.session.add(activity)
        db.session.commit()

    except Exception as e:

        db.session.rollback()
        print("Activity logging error:", e)