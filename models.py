from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.Text, default='')
    github_link = db.Column(db.String(200), default='')
    profile_image = db.Column(db.String(120), default='default.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    snippets = db.relationship('CodeSnippet', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    note_likes = db.relationship('NoteLike', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    snippets = db.relationship('CodeSnippet', backref='project', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.name}>'


class CodeSnippet(db.Model):
    __tablename__ = 'code_snippets'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), default='python')
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=None, onupdate=lambda: datetime.now(timezone.utc))
    edited_by = db.Column(db.String(80), default=None)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    comments = db.relationship('Comment', backref='snippet', lazy='dynamic',
                               primaryjoin='Comment.snippet_id == CodeSnippet.id',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CodeSnippet {self.title}>'


class ClassNote(db.Model):
    __tablename__ = 'class_notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False, default='')
    created_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    history = db.relationship('ClassNoteHistory', backref='note', lazy='dynamic',
                              order_by='ClassNoteHistory.edited_at.desc()')
    comments = db.relationship('Comment', backref='class_note', lazy='dynamic',
                               primaryjoin='Comment.note_id == ClassNote.id',
                               cascade='all, delete-orphan')
    likes = db.relationship('NoteLike', backref='note', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ClassNote {self.title}>'


class ClassNoteHistory(db.Model):
    __tablename__ = 'class_note_history'

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('class_notes.id', ondelete='SET NULL'), nullable=True)
    previous_content = db.Column(db.Text, nullable=False, default='')
    edited_by = db.Column(db.String(80), nullable=False)
    action_type = db.Column(db.String(20), nullable=False)
    edited_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ClassNoteHistory note={self.note_id} action={self.action_type}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    snippet_id = db.Column(db.Integer, db.ForeignKey('code_snippets.id'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('class_notes.id'), nullable=True)

    def __repr__(self):
        return f'<Comment {self.id} by user {self.author_id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(30), nullable=False)
    target_type = db.Column(db.String(30), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('activities', lazy='dynamic'))

    def __repr__(self):
        return f'<ActivityLog {self.action_type} by user {self.user_id}>'


class InviteCode(db.Model):
    __tablename__ = 'invite_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    created_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    used_by = db.Column(db.String(80), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<InviteCode {self.code}>'


class NoteLike(db.Model):
    __tablename__ = 'note_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('class_notes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<NoteLike user={self.user_id} note={self.note_id}>'

