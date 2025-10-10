from flask import render_template, request
from flask import current_app as app
from modules import text_generation, image_handling, text_to_speech, video_search

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_answer', methods=['POST'])
def get_answer():
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
