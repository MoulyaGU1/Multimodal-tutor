from . import db
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
import uuid # <-- NEW IMPORT

# Association table for the many-to-many relationship between users and completed videos
user_video_completion = db.Table('user_video_completion',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('video_id', db.Integer, db.ForeignKey('video.id'), primary_key=True)
)

class User(db.Model):
    # CRITICAL FIX: Allows SQLAlchemy to safely handle duplicate imports
    __table_args__ = {'extend_existing': True} 
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User Profile Fields
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False) # Required for completeness
    dob = db.Column(db.String(20)) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    profile_pic = db.Column(db.String(120), nullable=False, default='default.png')
    
    # Secure Password Storage
    password_hash = db.Column(db.String(200), nullable=False) 

    # Relationships
    completed_videos = db.relationship('Video', secondary=user_video_completion, lazy='dynamic',
                                       backref=db.backref('completed_by_users', lazy=True))
    quiz_history = db.relationship('QuizHistory', backref='user', lazy=True, foreign_keys='QuizHistory.user_id')

    # --- DEFENSIVE CONSTRUCTOR FIX ---
    def __init__(self, **kwargs):
        """
        Custom constructor to handle missing required fields (username) 
        and the legacy 'password' keyword argument.
        """
        raw_password = kwargs.pop('password', None) # Safely extract 'password' if present
        
        # FIX: Generate a username if none is explicitly provided, to satisfy NOT NULL constraint.
        if 'username' not in kwargs or kwargs['username'] is None:
            # Use a sanitized version of the first name and a short UUID part for uniqueness
            first_name = kwargs.get('first_name', 'user')
            sanitized_name = ''.join(c for c in first_name.lower() if c.isalnum())
            unique_suffix = str(uuid.uuid4())[:8] # First 8 chars of a UUID
            kwargs['username'] = f"{sanitized_name}_{unique_suffix}"
            
        # Call the default declarative base constructor with remaining arguments
        super().__init__(**kwargs)
        
        # Set the password using the secure method if a raw password was provided
        if raw_password:
            self.set_password(raw_password)
            
    # --- END DEFENSIVE CONSTRUCTOR FIX ---

    def set_password(self, password):
        """Hashes the plain text password for secure storage."""
        # Note: If you used generate_password_hash with a method in seed.py,
        # ensure the same hashing method is used here or rely on the default.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the stored hash against a provided password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Course(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(50), nullable=False)
    
    videos = db.relationship('Video', backref='course', lazy=True, cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.title}>'


class Video(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    video_url = db.Column(db.String(300), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def __repr__(self):
        return f'<Video {self.title}>'


class Quiz(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    def __repr__(self):
        return f'<Quiz Q{self.id} for Course {self.course_id}>'


class QuizHistory(db.Model):
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    
    results_detail = db.Column(db.Text, nullable=True) 

    def __repr__(self):
        return f'<QuizHistory {self.topic} - {self.score}/{self.total_questions}>'

    @property
    def detail(self):
        """Returns the results_detail string loaded as a Python list/dict."""
        if self.results_detail:
            return json.loads(self.results_detail)
        return []
    
