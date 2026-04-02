import os
from flask import Flask

def create_app():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "app", "templates"),
        static_folder=os.path.join(BASE_DIR, "static")
    )

    app.secret_key = "supersecretkey"

    from .routes import main
    app.register_blueprint(main)

    return app