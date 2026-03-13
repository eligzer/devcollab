import uuid
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, InviteCode, User
from forms import InviteCodeForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator that restricts access to admin users only."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    codes = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
    return render_template('admin/dashboard.html', users=users, codes=codes)


@admin_bp.route('/invite-codes', methods=['GET', 'POST'])
@admin_required
def invite_codes():
    form = InviteCodeForm()
    if form.validate_on_submit():
        count = form.count.data
        new_codes = []
        for _ in range(count):
            code_str = uuid.uuid4().hex[:12].upper()
            code = InviteCode(code=code_str, created_by=current_user.username)
            db.session.add(code)
            new_codes.append(code_str)
        db.session.commit()
        flash(f'Generated {count} invite code(s): {", ".join(new_codes)}', 'success')
        return redirect(url_for('admin.invite_codes'))

    codes = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
    return render_template('admin/invite_codes.html', form=form, codes=codes)


@admin_bp.route('/invite-codes/<int:code_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_code(code_id):
    code = InviteCode.query.get_or_404(code_id)
    code.is_active = False
    db.session.commit()
    flash(f'Invite code {code.code} deactivated.', 'info')
    return redirect(url_for('admin.invite_codes'))


@admin_bp.route('/seed-admin')
def seed_admin():
    """One-time route to create the first admin user + invite code.
    Only works when no admin exists yet."""
    if User.query.filter_by(is_admin=True).first():
        flash('Admin already exists.', 'warning')
        return redirect(url_for('main.index'))

    # Create admin user
    admin = User(username='admin', email='admin@devcollab.local', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)

    # Create a starter invite code
    starter_code = InviteCode(code='WELCOME2026', created_by='admin')
    db.session.add(starter_code)

    db.session.commit()
    flash('Admin account created (admin / admin123). Starter invite code: WELCOME2026', 'success')
    return redirect(url_for('auth.login'))


@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot modify another admin account.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "reactivated" if user.is_active else "suspended"
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.dashboard'))
