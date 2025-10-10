import os
from gtts import gTTS

# Define the path where audio files will be stored
AUDIO_FOLDER = os.path.join('app', 'static', 'audio')

# Ensure the audio directory exists
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def generate_audio(text):
    """
    Converts a string of text into an MP3 audio file using gTTS.
    It saves the file and returns a URL path to it.
    """
    try:
        # Create a unique, predictable filename based on the text's hash
        # This prevents re-generating the same file and is very efficient
        filename = f"speech_{hash(text)}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        file_url = f'/static/audio/{filename}'

        # If the file doesn't already exist, create it
        if not os.path.exists(filepath):
            print(f"Generating new audio file: {filepath}")
            # Create the gTTS object
            tts = gTTS(text=text, lang='en', slow=False)
            # Save the audio file
            tts.save(filepath)
        else:
            print(f"Audio file already exists: {filepath}")

        # Return the URL path that the HTML can use
        return file_url

    except Exception as e:
        print(f"An error occurred in generate_audio: {e}")
        # Return None or a placeholder if an error occurs
        return None
