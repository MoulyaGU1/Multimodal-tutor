from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from .config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Load environment variables
    load_dotenv()

    # Create Flask app
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates')
    app.config.from_object(Config)

    # Initialize extensions
    CORS(app)  # Enable CORS
    db.init_app(app)
    migrate.init_app(app, db)

    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)

    with app.app_context():
        # Import models (important for Flask-Migrate to detect them)
        from . import models

        # Import and register blueprint
        from . import routes
        app.register_blueprint(routes.main)

    return app
