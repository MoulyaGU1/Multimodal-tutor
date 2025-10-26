# modules/chatbot.py
import os
import google.generativeai as genai
import traceback
import logging

# Set up logging early for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
api_key = os.getenv("GEMINI_API_KEY")
gemini_configured_chat = False 

if api_key:
    try:
        # Configure the client globally for all subsequent calls
        genai.configure(api_key=api_key)
        gemini_configured_chat = True
        logging.info("Gemini API configured successfully in modules/chatbot.py.")
    except Exception as config_err:
        logging.error(f"Failed to configure Gemini API in modules/chatbot.py: {config_err}")
else:
    logging.warning("GEMINI_API_KEY not found or empty for chatbot module.")


# --- Chatbot Response Function (Single-Turn) ---
def get_response(user_input: str) -> str:
    """
    Gets a conversational response from the Gemini API without maintaining history.
    This is useful for quick, stateless queries.
    """
    logging.debug(f"chatbot.get_response called with input: '{user_input}'")
    if not gemini_configured_chat:
        logging.error("chatbot.get_response cannot run, API key not configured.")
        return "Chatbot service not configured (missing or invalid API key)."

    try:
        # Use a non-chat model for stateless queries
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Add a system instruction here for context in stateless mode
        system_instruction = "You are a friendly, concise, and helpful study assistant."
        
        prompt = f"{system_instruction}\n\nUser: {user_input}"
        
        logging.debug("Sending stateless prompt to Gemini...")
        response = model.generate_content(prompt)

        if response.parts:
            logging.debug("Received chat response from Gemini.")
            return response.text.strip()
        else:
            # Handle blocked/empty response logic
            feedback = getattr(response, 'prompt_feedback', None)
            reason = getattr(feedback, 'block_reason', 'Unknown') if feedback else 'Unknown'
            logging.warning(f"Chatbot response blocked. Reason: {reason}")
            return f"I couldn't generate a response for that. Reason: {reason}"

    except Exception as e:
        error_msg = f"An unexpected error occurred during chatbot response generation: {type(e).__name__} - {e}"
        logging.error(error_msg)
        logging.exception("Traceback for chatbot error:")
        return "Sorry, an unexpected error occurred while contacting the AI service. Please check server logs."