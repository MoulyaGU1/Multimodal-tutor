from app import create_app
from app import create_app, db

# Initialize the Flask application using the factory function
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
# Create database tables if they do not exist.
# This must be done inside the application context.
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # The application will now run, serving routes from app/routes.py
    app.run(debug=True)