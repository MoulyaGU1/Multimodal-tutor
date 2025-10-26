# run.py
import os # Add os import if not already there
from dotenv import load_dotenv

load_dotenv() # Loads variables from .env

# --- ADD THIS LINE ---
print(f"DEBUG run.py: GEMINI_API_KEY = {os.getenv('GEMINI_API_KEY')}")
# --------------------

from app import create_app, db
# ... rest of your run.py code ...

app = create_app()

# ... shell context processor ...

if __name__ == '__main__':
    app.run(debug=True)