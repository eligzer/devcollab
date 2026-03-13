from flask import Blueprint, render_template, request
from flask_login import current_user
from sqlalchemy import or_

from models import db, User, Project, ClassNote

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # pass current_user to template safely
    return render_template('index.html', current_user=current_user)


@main_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()

    users = []
    projects = []
    notes = []

    if query:
        search_filter = f"%{query}%"

        users = User.query.filter(
            User.username.ilike(search_filter)
        ).all()

        projects = Project.query.filter(
            or_(
                Project.title.ilike(search_filter),
                Project.description.ilike(search_filter)
            )
        ).all()

        notes = ClassNote.query.filter(
            or_(
                ClassNote.title.ilike(search_filter),
                ClassNote.content.ilike(search_filter)
            )
        ).all()

    return render_template(
        'search_results.html',
        query=query,
        users=users,
        projects=projects,
        notes=notes,
        current_user=current_user
    )