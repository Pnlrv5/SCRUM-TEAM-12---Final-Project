import os
from flask import Flask
from app.database import db
from app.routes import routes
from app.models import AdminUser

def create_app():
    app = Flask(__name__)

    # Absolute path to database (VERY IMPORTANT)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "reservations.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "secret-key"

    # 🔍 DEBUG LINE (TEMPORARY – KEEP FOR NOW)
    print("USING DB:", app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)
    app.register_blueprint(routes)

    # Create tables + seed admin
    with app.app_context():
        db.create_all()

        if not AdminUser.query.first():
            db.session.add(
                AdminUser(username="admin", password_hash="admin123")
            )
            db.session.commit()

    return app
