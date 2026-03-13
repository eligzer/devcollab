import os
from flask import Flask
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User
from extensions import socketio

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # Upload folder
    upload_folder = os.path.join(app.root_path, "static", "profile_pics")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    # Security
    CSRFProtect(app)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Flask-Login loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.projects import projects_bp
    from routes.snippets import snippets_bp
    from routes.notes import notes_bp
    from routes.activity import activity_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.messages import messages_bp
    from routes.ai import ai_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(snippets_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(ai_bp)

    # Notification count injector
    @app.context_processor
    def inject_notifications():

        if current_user.is_authenticated:
            from models import Notification

            count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()

            return dict(unread_notifications_count=count)

        return dict(unread_notifications_count=0)

    # Import socket events
    import events

    # Database initialization
    with app.app_context():
        try:

            db.create_all()

            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin_password = os.environ.get("ADMIN_PASSWORD", "elixer")
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")

            admin = User.query.filter_by(username=admin_username).first()

            if admin is None:

                admin = User(
                    username=admin_username,
                    email=admin_email,
                    is_admin=True
                )

                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()

                print("Admin user created")

            else:

                admin.set_password(admin_password)
                db.session.commit()

                print("Admin password synced")

        except Exception as e:

            db.session.rollback()
            print("Database initialization error:", e)

    return app


# Create app instance for Gunicorn
app = create_app()