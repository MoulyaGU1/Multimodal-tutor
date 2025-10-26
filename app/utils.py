# modules/utils.py

from modules.text_generation import generate_text
from modules.image_handling import generate_image
from modules.text_to_speech import text_to_speech_audio

def generate_answer(prompt):
    """
    Generate an AI answer for a given prompt.
    Can call your text_generation module.
    """
    return generate_text(prompt)  # assuming generate_text exists in text_generation.py

def generate_images(prompt):
    """Generate images from prompt"""
    return generate_image(prompt)  # assuming generate_image exists

def generate_audio_from_text(text):
    """Generate audio from text"""
    return text_to_speech_audio(text)  # assuming function exists
