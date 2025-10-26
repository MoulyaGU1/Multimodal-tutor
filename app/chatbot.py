import os
import google.generativeai as genai

# Load API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_chatbot_response(prompt):
    try:
        response = genai.chat.create(
            model="gemini-2.5-flash",
            messages=[{"author": "user", "content": prompt}]
        )
        return response.last.strip()
    except Exception as e:
        print("Error contacting Gemini API:", e)
        return "Sorry, I couldn't process your request."
