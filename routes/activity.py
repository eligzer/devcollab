from flask import Blueprint, render_template
from models import ActivityLog

activity_bp = Blueprint('activity', __name__)


@activity_bp.route('/activity')
def feed():
    activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(50).all()
    return render_template('activity/feed.html', activities=activities)
