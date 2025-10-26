from app import app  # Import your Flask app
from vercel_wsgi import handle_request

def handler(request, response):
    return handle_request(app, request, response)
