from flask import Flask
from .config import Config
from dotenv import load_dotenv
import os

def create_app():
    # ✅ Load environment variables before creating app
    load_dotenv()

    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    with app.app_context():
        from . import routes

    return app
