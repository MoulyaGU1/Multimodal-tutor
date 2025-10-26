import click
from app import create_app, db
from app.models import User, Course, Video, Quiz
from werkzeug.security import generate_password_hash

# --- Sample Data ---
users_data = [
    {'first_name': 'Admin', 'last_name': 'User', 'dob': '2000-01-01', 'email': 'admin@example.com', 'password': 'password123'},
    {'first_name': 'Test', 'last_name': 'User', 'dob': '1995-05-10', 'email': 'test@example.com', 'password': 'password456'}
]

courses_data = [
    {'id': 1, 'title': 'Introduction to Python', 'description': 'Learn the basics of Python programming, including data types, control flow, and functions.', 'level': 'Beginner'},
    {'id': 2, 'title': 'Data Structures & Algorithms', 'description': 'In-depth study of common data structures and essential algorithms for problem-solving.', 'level': 'Intermediate'},
    {'id': 3, 'title': 'Web Development with Flask', 'description': 'Build dynamic web applications using the Flask framework and Jinja templating.', 'level': 'Intermediate'}
]

videos_data = [
    {'course_id': 1, 'title': 'Welcome to Python: Setup & Overview', 'video_url': 'https://www.youtube.com/embed/rfscVS0vtbw'},
    {'course_id': 1, 'title': 'Data Types and Variables', 'video_url': 'https://www.youtube.com/embed/k9WqpQp8OfE'},
    {'course_id': 2, 'title': 'Arrays vs Linked Lists', 'video_url': 'https://www.youtube.com/embed/R-u87D70WwY'},
    {'course_id': 3, 'title': 'Introduction to Flask', 'video_url': 'https://www.youtube.com/embed/Z0oY178qU08'},
]

quizzes_data = [
    {'course_id': 1, 'question': 'What is Python?', 'answer': 'Programming Language'},
    {'course_id': 1, 'question': 'Which data structure is ordered and mutable?', 'answer': 'List'},
]

def seed_database():
    """Drops, creates, and seeds the database with sample data."""
    
    # Create an app instance and push an application context
    app = create_app()
    with app.app_context():
        print("-> Dropping all tables...")
        db.drop_all()
        print("-> Creating all tables...")
        db.create_all()

        # --- Seed Users ---
        print("-> Seeding users...")
        for data in users_data:
            hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
            user = User(
                first_name=data['first_name'],
                last_name=data['last_name'],
                dob=data['dob'],
                email=data['email'],
                password=hashed_password
            )
            db.session.add(user)
        # Commit users first so they get IDs
        db.session.commit()
        print(f"-> VERIFY: Found {User.query.count()} users in DB.")

        # --- Seed Courses, Videos, Quizzes ---
        print("-> Seeding courses...")
        for data in courses_data:
            db.session.add(Course(**data))
        
        print("-> Seeding videos...")
        for data in videos_data:
            db.session.add(Video(**data))

        print("-> Seeding quizzes...")
        for data in quizzes_data:
            db.session.add(Quiz(**data))
        
        # Commit the rest of the data
        db.session.commit()
        print(f"-> VERIFY: Found {Course.query.count()} courses in DB.")
        print("\nDatabase has been successfully seeded! 🌱")

# This allows you to run 'python seed.py' from your terminal
if __name__ == '__main__':
    seed_database()