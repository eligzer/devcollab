from werkzeug.utils import secure_filename
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, ClassNote, ClassNoteHistory, Comment, NoteLike, User, Notification
from forms import ClassNoteForm, CommentForm, SearchForm
from utils import log_activity
from datetime import datetime, timezone

notes_bp = Blueprint('notes', __name__, url_prefix='/notes')


@notes_bp.route('/')
def list_notes():
    notes = ClassNote.query.order_by(ClassNote.updated_at.desc()).all()
    # Need an empty SearchForm for the list page if no global search bar is present without it
    # But usually global search is handled by navbar form pointing to /notes/search
    return render_template('notes/list.html', notes=notes)


@notes_bp.route('/search')
def search_notes():
    query = request.args.get('q', '')
    if query:
        search_filter = f"%{query}%"
        notes = ClassNote.query.filter(
            or_(
                ClassNote.title.ilike(search_filter),
                ClassNote.content.ilike(search_filter)
            )
        ).order_by(ClassNote.updated_at.desc()).all()
    else:
        notes = []
    
    return render_template('notes/search_results.html', notes=notes, query=query)


@notes_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_note():
    form = ClassNoteForm()
    if form.validate_on_submit():
        note = ClassNote(
            title=form.title.data,
            content=form.content.data,
            created_by=current_user.username
        )
        db.session.add(note)
        db.session.flush()

        history = ClassNoteHistory(
            note_id=note.id,
            previous_content=form.content.data,
            edited_by=current_user.username,
            action_type='create'
        )
        db.session.add(history)
        log_activity(current_user.id, 'create_note', 'note', note.id,
                     f'{current_user.username} created the Class Note "{note.title}"')
        db.session.commit()
        flash('Note created!', 'success')
        return redirect(url_for('notes.detail', note_id=note.id))

    return render_template('notes/create.html', form=form)


@notes_bp.route('/<int:note_id>')
def detail(note_id):
    note = ClassNote.query.get_or_404(note_id)
    last_edit = note.history[0] if note.history else None
    comments = note.comments.order_by(Comment.created_at.asc()).all()
    comment_form = CommentForm()
    return render_template('notes/detail.html', note=note, last_edit=last_edit,
                           comments=comments, comment_form=comment_form)


@notes_bp.route('/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = ClassNote.query.get_or_404(note_id)
    form = ClassNoteForm(obj=note)

    if form.validate_on_submit():
        history = ClassNoteHistory(
            note_id=note.id,
            previous_content=note.content,
            edited_by=current_user.username,
            action_type='edit'
        )
        db.session.add(history)

        note.title = form.title.data
        note.content = form.content.data
        note.updated_at = datetime.now(timezone.utc)
        
        log_activity(current_user.id, 'edit_note', 'note', note.id,
                     f'{current_user.username} edited the Class Note "{note.title}"')
        db.session.commit()
        flash('Note updated!', 'success')
        return redirect(url_for('notes.detail', note_id=note.id))

    return render_template('notes/edit.html', form=form, note=note)


@notes_bp.route('/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = ClassNote.query.get_or_404(note_id)
    note_title = note.title

    history = ClassNoteHistory(
        note_id=note.id,
        previous_content=note.content,
        edited_by=current_user.username,
        action_type='delete'
    )
    db.session.add(history)
    log_activity(current_user.id, 'delete_note', 'note', note.id,
                 f'{current_user.username} deleted the Class Note "{note_title}"')
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted. The edit history has been preserved.', 'info')
    return redirect(url_for('notes.list_notes'))


@notes_bp.route('/<int:note_id>/history')
def history(note_id):
    note = ClassNote.query.get(note_id)
    entries = ClassNoteHistory.query.filter_by(note_id=note_id) \
        .order_by(ClassNoteHistory.edited_at.asc()).all()

    if not entries and not note:
        flash('No history found for this note.', 'warning')
        return redirect(url_for('notes.list_notes'))

    return render_template('notes/history.html', note=note, entries=entries, note_id=note_id)


@notes_bp.route('/<int:note_id>/comment', methods=['POST'])
@login_required
def comment_note(note_id):
    note = ClassNote.query.get_or_404(note_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            author_id=current_user.id,
            note_id=note.id
        )
        db.session.add(comment)
        db.session.flush()
        
        # Notify note author if not the same user
        note_author = User.query.filter_by(username=note.created_by).first()
        if note_author and note_author.id != current_user.id:
            notif = Notification(user_id=note_author.id, message=f'{current_user.username} commented on your note "{note.title}"')
            db.session.add(notif)
            
        log_activity(current_user.id, 'comment', 'comment', comment.id,
                     f'{current_user.username} commented on Class Note "{note.title}"')
        db.session.commit()
            
        flash('Comment posted!', 'success')
    return redirect(url_for('notes.detail', note_id=note.id))


@notes_bp.route('/<int:note_id>/like', methods=['POST'])
@login_required
def toggle_like(note_id):
    note = ClassNote.query.get_or_404(note_id)
    
    existing_like = NoteLike.query.filter_by(user_id=current_user.id, note_id=note.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        # Optionally log unlike activity here, or just let users silently toggle.
    else:
        new_like = NoteLike(user_id=current_user.id, note_id=note.id)
        db.session.add(new_like)
        
        # Notify note author if not the same user
        note_author = User.query.filter_by(username=note.created_by).first()
        if note_author and note_author.id != current_user.id:
            notif = Notification(user_id=note_author.id, message=f'{current_user.username} liked your note "{note.title}"')
            db.session.add(notif)
            
        db.session.commit()
            
        log_activity(current_user.id, 'like_note', 'note', note.id,
                     f'{current_user.username} liked the Class Note "{note.title}"')
                     
    return redirect(request.referrer or url_for('notes.detail', note_id=note.id))


@notes_bp.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        
        uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        filepath = os.path.join(uploads_dir, unique_filename)
        file.save(filepath)
        
        file_url = url_for('static', filename='uploads/' + unique_filename)
        return jsonify({'url': file_url})
        
    return jsonify({'error': 'Invalid file type.'}), 400
