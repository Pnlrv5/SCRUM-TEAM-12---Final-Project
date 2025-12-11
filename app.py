from flask_sqlalchemy import SQLAlchemy
from app.database import db
from flask import Flask
from app.routes import routes

def create_app():
    app = Flask(__name__)

    #SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reservations.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "secret-key"

    db.init_app(app)
    app.register_blueprint(routes)
    with app.app_context():
        db.create_all()
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
