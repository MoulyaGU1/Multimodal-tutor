from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from .config import Config # Importing the Config class

# Initialize the SQLAlchemy object outside the factory function
# This allows models and routes to easily import and use it.
db = SQLAlchemy()

# --- User Model Definition ---
class User(db.Model):
    """Database model for application users."""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(100), default="default.png")

    def __repr__(self):
        return f"User('{self.email}')"


def create_app():
    # 1. Load environment variables before creating app
    load_dotenv()

    # 2. Initialize Flask App
    # Setting instance_relative_config=True helps Flask find files in the 'instance' folder.
    app = Flask(__name__, 
                instance_relative_config=True, 
                template_folder='../templates')
    
    # 3. Load configuration from the Config class
    app.config.from_object(Config)

    # 4. Initialize Flask extensions
    db.init_app(app)
    
    # Ensure the upload directory exists using the configured path
    os.makedirs(app.config.get('UPLOAD_FOLDER'), exist_ok=True)
    
    with app.app_context():
        # 5. Import routes and register them
        # Note: routes.py will import 'db' and 'User' from this file
        from . import routes 
        
        # 6. Create database tables if they don't exist
        # This will create the users.db file in the 'instance' folder if it doesn't exist
        db.create_all()

    return app
