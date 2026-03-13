import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User


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

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(snippets_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    # Database initialization
    with app.app_context():
        db.create_all()

        # Bootstrap admin user
        admin_exists = User.query.filter_by(is_admin=True).first()

        if not admin_exists:
            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")

            admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )

            admin.set_password(admin_password)

            db.session.add(admin)

            try:
                db.session.commit()
                print(f"Admin user created: {admin_username}")
            except Exception as e:
                db.session.rollback()
                print(f"Admin bootstrap error: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)