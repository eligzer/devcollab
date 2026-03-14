from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from models import db, User, Project, ClassNote, Comment, CommentLike, Notification

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

        projects = Project.query.options(
            joinedload(Project.owner),
            joinedload(Project.snippets)
        ).filter(
            or_(
                Project.name.ilike(search_filter),
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
        notes=notes,
        current_user=current_user
    )

@main_bp.route('/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def toggle_comment_like(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    existing_like = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
    else:
        new_like = CommentLike(user_id=current_user.id, comment_id=comment.id)
        db.session.add(new_like)
        
        if comment.author_id != current_user.id:
            link = None
            if comment.note_id:
                link = url_for('notes.detail', note_id=comment.note_id)
            elif comment.snippet_id:
                link = url_for('snippets.detail', snippet_id=comment.snippet_id)
                
            notif = Notification(
                user_id=comment.author_id,
                message=f'{current_user.username} liked your comment.',
                link=link
            )
            db.session.add(notif)
            
        db.session.commit()
        
    return redirect(request.referrer or url_for('main.index'))