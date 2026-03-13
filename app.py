import os
from flask_wtf.csrf import CSRFProtect
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'



def create_app():
    app = Flask(__name__)

    # Load configuration first
    app.config.from_object(Config)
    
    # Configure upload folder for profile pictures
    upload_folder = os.path.join(app.root_path, 'static', 'profile_pics')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    # Security
    csrf = CSRFProtect(app)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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

    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Bootstrap Admin User
        admin_exists = User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            import os
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            
            new_admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )
            new_admin.set_password(admin_password)
            db.session.add(new_admin)
            try:
                db.session.commit()
                print(f"Bootstrapped default admin user: {admin_username}")
            except Exception as e:
                db.session.rollback()
                print(f"Error bootstrapping admin user: {e}")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
