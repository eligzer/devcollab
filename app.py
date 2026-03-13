import os
from flask import Flask
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User
from extensions import socketio

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Configure upload folder
    upload_folder = os.path.join(app.root_path, "static", "profile_pics")
    app.config["UPLOAD_FOLDER"] = upload_folder

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Security
    CSRFProtect(app)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
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

    # Notification injector
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

    # Import socket events
    import events

    # Database setup
    with app.app_context():

        db.create_all()

        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "elixer")
        admin_email = os.environ.get("ADMIN_EMAIL", "eligzerr@gmail.com")

        admin = User.query.filter_by(username=admin_username).first()

        if not admin:
            admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )

            admin.set_password(admin_password)
            db.session.add(admin)

            try:
                db.session.commit()
                print("Admin user created successfully")
            except Exception as e:
                db.session.rollback()
                print(f"Admin creation error: {e}")

        else:
            admin.set_password(admin_password)

            try:
                db.session.commit()
                print("Admin password synced with environment variable")
            except Exception as e:
                db.session.rollback()
                print(f"Admin update error: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(app, debug=True)