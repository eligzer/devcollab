from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin = User.query.filter_by(username="admin").first()

    if admin:
        admin.password_hash = generate_password_hash("elixer")
        db.session.commit()
        print("Admin password updated")
    else:
        print("Admin user not found")