import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, User, ClassNote
from forms import EditProfileForm
from utils import log_activity
import uuid

user_bp = Blueprint('user', __name__)


@user_bp.route('/user/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    notes = ClassNote.query.filter_by(created_by=user.username).order_by(ClassNote.created_at.desc()).all()
    return render_template('user/profile.html', user=user, notes=notes)


@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, obj=current_user)
    if form.validate_on_submit():
        if form.profile_image.data:
            pic_file = form.profile_image.data
            # Generate unique filename
            filename = secure_filename(pic_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            pic_file.save(pic_path)
            current_user.profile_image = unique_filename
        
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.github_link = form.github_link.data
        db.session.commit()
        
        log_activity(current_user.id, 'update_profile', 'user', current_user.id,
                     f'{current_user.username} updated their profile')
        
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user.profile', username=current_user.username))
        
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.bio.data = current_user.bio
        form.github_link.data = current_user.github_link
        
    return render_template('user/edit_profile.html', form=form)
