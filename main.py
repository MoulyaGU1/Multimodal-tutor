# main.py
from app import create_app

app = create_app()

# Vercel uses this script as entrypoint. Don't set debug=True for production.
if __name__ == "__main__":
    app.run()
