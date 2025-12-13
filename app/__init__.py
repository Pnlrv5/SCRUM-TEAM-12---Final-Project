import os
from flask import Flask
from app.database import db
from app.routes import routes
from app.models import AdminUser

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__)

    db_path = os.path.join(base_dir, "reservations.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "secret-key"

    db.init_app(app)
    app.register_blueprint(routes)

    with app.app_context():
        db.create_all()
        if not AdminUser.query.first():
            db.session.add(AdminUser(username="admin", password_hash="admin123"))
            db.session.commit()

    return app
