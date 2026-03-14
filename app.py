import os
import logging

from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text


from config import Config
from models import db, User, Notification

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# ----------------------------
# Extensions
# ----------------------------

login_manager = LoginManager()
csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


# ----------------------------
# Application Factory
# ----------------------------

def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static"
    )

    app.config.from_object(Config)
  
    

    # ----------------------------
    # Logging
    # ----------------------------

    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # ----------------------------
    # Upload Folder Setup
    # ----------------------------

    upload_folder = os.path.join(app.root_path, "static", "profile_pics")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    # ----------------------------
    # Initialize Extensions
    # ----------------------------

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # ----------------------------
    # DATABASE AUTO REPAIR
    # ----------------------------

    with app.app_context():

        try:

            db.create_all()

            db.session.execute(text("""
                ALTER TABLE notifications
                ADD COLUMN IF NOT EXISTS link VARCHAR(255)
            """))

            db.session.execute(text("""
                ALTER TABLE activity_log
                ADD COLUMN IF NOT EXISTS action VARCHAR(50)
            """))

            db.session.execute(text("""
                ALTER TABLE activity_log
                ADD COLUMN IF NOT EXISTS target_type VARCHAR(50)
            """))

            db.session.execute(text("""
                ALTER TABLE activity_log
                ADD COLUMN IF NOT EXISTS target_id INTEGER
            """))

            db.session.execute(text("""
                ALTER TABLE activity_log
                ADD COLUMN IF NOT EXISTS description TEXT
            """))

            db.session.commit()

            app.logger.info("Database schema verified.")

        except Exception as e:

            db.session.rollback()
            app.logger.error(f"Database initialization error: {e}")

    # ----------------------------
    # Flask Login Loader
    # ----------------------------

    @login_manager.user_loader
    def load_user(user_id):

        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            app.logger.error(f"User loader error: {e}")
            return None

    # ----------------------------
    # Register Blueprints
    # ----------------------------

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

    # ----------------------------
    # Notification Counter
    # ----------------------------

    @app.context_processor
    def inject_notifications():

        if current_user.is_authenticated:

            try:

                count = Notification.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).count()

                return dict(unread_notifications_count=count)

            except Exception as e:

                app.logger.error(f"Notification query error: {e}")
                return dict(unread_notifications_count=0)

        return dict(unread_notifications_count=0)

    # ----------------------------
    # Error Handlers
    # ----------------------------

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):

        try:
            db.session.rollback()
        except:
            pass

        return render_template("errors/500.html"), 500

    return app


# ----------------------------
# App Instance
# ----------------------------

app = create_app()


# ----------------------------
# Local Development
# ----------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )