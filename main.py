from flask import Flask, render_template, request
import os

app = Flask(__name__)

# Example route
@app.route("/")
def home():
    return "Hello, Multimodal Tutor!"

# Example of environment variable usage
@app.route("/youtube")
def youtube():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    return f"Your YouTube API key is: {api_key}"
