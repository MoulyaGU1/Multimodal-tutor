from flask import render_template, request, redirect, url_for, flash, session
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import os
import json # <-- NEW: Needed to handle the JSON string in the user progress column
from flask import Flask, render_template, request, redirect, url_for, session, g



# Import necessary modules/objects from the local application package
# db and User are defined in app/_init_.py
from . import db, User 
from modules import text_generation, image_handling, text_to_speech, video_search 


# --- Authentication Helper ---

def allowed_file(filename):
    """Checks if the file extension is allowed for profile picture uploads."""
    # Uses the ALLOWED_EXTENSIONS defined in app/config.py
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Core Application Flow Routes ---

@app.route('/')
def home():
    """Root route: Redirects logged-in users to the tutor index, otherwise to login."""
    if 'user_id' in session:
        return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/tutor-index')
def tutor_index():
    """The main index page for the multimodal tutor. Requires login."""
    if 'user_id' not in session:
        flash("Please log in to access the tutor.", "warning")
        return redirect(url_for('login'))
    
    # Render the main tutor interface
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():
    """Handles multimodal query processing. Requires login."""
    if 'user_id' not in session:
        flash("Please log in to access the tutor.", "warning")
        return redirect(url_for('login'))
        
    query = request.form.get('query')
    if not query:
        return "Error: A question is required.", 400

    # Generate text answer
    text_answer = text_generation.generate_text_answer(query)

    # Generate audio from text
    audio_url = text_to_speech.generate_audio(text_answer)

    # Get top 3 YouTube videos
    top_videos = video_search.find_top_videos(query, max_results=3)

    # Get top 3 relevant images
    top_images = image_handling.find_relevant_images(query, max_results=3)

    return render_template(
        'lesson.html',
        query=query,
        text_answer=text_answer,
        audio_url=audio_url,
        top_videos=top_videos,
        top_images=top_images
    )
    
# --- Authentication Routes (Copied and adapted from login_app/app.py) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = request.form['dob']
        email = request.form['email']
        password = request.form['password']

        # Use db.session.execute for querying
        existing_user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(first_name=first_name, last_name=last_name, dob=dob, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handles user logout by clearing the session."""
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Update profile fields
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.dob = request.form['dob']

        # Update profile picture if uploaded
        if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
         pic = request.files['profile_pic']
         pic_filename = secure_filename(pic.filename)
         pic_path = os.path.join(app.config['UPLOAD_FOLDER'], pic_filename)
         pic.save(pic_path)
         user.profile_pic = pic_filename
         


        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    # Ensure profile_pic is never None
    if not user.profile_pic:
        user.profile_pic = 'default.png'

    return render_template('profile.html', user=user)

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    current = request.form['current_password']
    new = request.form['new_password']
    confirm = request.form['confirm_password']

    if not check_password_hash(user.password, current):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for('profile'))

    if new != confirm:
        flash("New passwords do not match.", "danger")
        return redirect(url_for('profile'))

    user.password = generate_password_hash(new, method='pbkdf2:sha256')
    db.session.commit()
    flash("Password changed successfully!", "success")
    return redirect(url_for('profile'))
   # Basic password length check (optional, but good practice)


    u
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)