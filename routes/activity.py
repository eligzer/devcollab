from flask import Blueprint, render_template
from models import Activity
from sqlalchemy.orm import joinedload

activity_bp = Blueprint('activity', __name__)


@activity_bp.route('/activity')
def feed():
    activities = Activity.query.options(joinedload(Activity.user)).order_by(Activity.created_at.desc()).limit(50).all()
    return render_template('activity/feed.html', activities=activities)
