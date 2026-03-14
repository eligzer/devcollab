from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ======================
# USER
# ======================
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    password_hash = db.Column(db.String(256), nullable=False)

    bio = db.Column(db.Text, default="")
    github_link = db.Column(db.String(200), default="")
    profile_image = db.Column(db.String(120), default="default.jpg")

    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    projects = db.relationship("Project", backref="owner", lazy=True)
    snippets = db.relationship("CodeSnippet", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)

    links = db.relationship("UserLink", backref="user", lazy=True, cascade="all, delete-orphan")

    messages_sent = db.relationship(
        "Message",
        foreign_keys="Message.sender_id",
        backref="sender",
        lazy=True
    )

    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        backref="receiver",
        lazy=True
    )

    notifications = db.relationship(
        "Notification",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    activities = db.relationship(
        "ActivityLog",
        backref="user",
        lazy=True
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    def __repr__(self):

        return f"<User {self.username}>"


# ======================
# PROJECT
# ======================
class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(140), nullable=False)

    description = db.Column(db.Text, default="")

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    snippets = db.relationship(
        "CodeSnippet",
        backref="project",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return f"<Project {self.name}>"


# ======================
# CODE SNIPPET
# ======================
class CodeSnippet(db.Model):

    __tablename__ = "code_snippets"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(140), nullable=False)

    code = db.Column(db.Text, nullable=False)

    language = db.Column(db.String(50), default="python")

    description = db.Column(db.Text, default="")

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc)
    )

    edited_by = db.Column(db.String(80), nullable=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    comments = db.relationship(
        "Comment",
        backref="snippet",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return f"<CodeSnippet {self.title}>"


# ======================
# CLASS NOTES
# ======================
class ClassNote(db.Model):

    __tablename__ = "class_notes"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    content = db.Column(db.Text, nullable=False)

    created_by = db.Column(db.String(80), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    comments = db.relationship(
        "Comment",
        backref="class_note",
        lazy=True,
        cascade="all, delete-orphan"
    )

    likes = db.relationship(
        "NoteLike",
        backref="note",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return f"<ClassNote {self.title}>"


# ======================
# COMMENT
# ======================
class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    snippet_id = db.Column(
        db.Integer,
        db.ForeignKey("code_snippets.id"),
        nullable=True
    )

    note_id = db.Column(
        db.Integer,
        db.ForeignKey("class_notes.id"),
        nullable=True
    )

    def __repr__(self):

        return f"<Comment {self.id}>"


# ======================
# ACTIVITY LOG
# ======================
class ActivityLog(db.Model):

    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    action_type = db.Column(db.String(50), nullable=False)

    target_type = db.Column(db.String(50), nullable=False)

    target_id = db.Column(db.Integer, nullable=True)

    description = db.Column(db.String(500), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):

        return f"<ActivityLog {self.action_type}>"


# ======================
# INVITE CODE
# ======================
class InviteCode(db.Model):

    __tablename__ = "invite_codes"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(40), unique=True, nullable=False, index=True)

    created_by = db.Column(db.String(80), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    used_by = db.Column(db.String(80), nullable=True)

    used_at = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):

        return f"<InviteCode {self.code}>"


# ======================
# NOTE LIKE
# ======================
class NoteLike(db.Model):

    __tablename__ = "note_likes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    note_id = db.Column(
        db.Integer,
        db.ForeignKey("class_notes.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# ======================
# USER LINK
# ======================
class UserLink(db.Model):

    __tablename__ = "user_links"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(db.String(100), nullable=False)

    url = db.Column(db.String(500), nullable=False)


# ======================
# MESSAGE
# ======================
class Message(db.Model):

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    is_read = db.Column(db.Boolean, default=False)


# ======================
# NOTIFICATION
# ======================
class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message = db.Column(db.Text, nullable=False)

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )