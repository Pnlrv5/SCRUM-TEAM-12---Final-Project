import os
from flask import Flask
from app.routes import routes

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        instance_path=os.path.join(base_dir, "instance"),
        instance_relative_config=True,
    )

    app.secret_key = "dev-secret-key"

    app.register_blueprint(routes)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
