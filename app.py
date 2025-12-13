from flask import Flask
import os
from app.routes import routes, init_db

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        instance_path=os.path.join(base_dir, "instance"),
        instance_relative_config=True
    )

    app.secret_key = "dev-secret-key"

    with app.app_context():
        init_db()

    app.register_blueprint(routes)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
