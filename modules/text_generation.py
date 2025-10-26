import os
import google.generativeai as genai
import requests
import json
import traceback
from dotenv import load_dotenv
import logging

# Load environment variables (critical for both Gemini and Google Search)
load_dotenv()

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%s - %s - %s', datefmt='%Y-%m-%d %H:%M:%S')

# --- Configuration ---
# Gemini API configuration
api_key = os.getenv("GEMINI_API_KEY")
gemini_configured = False

if api_key:
    try:
        # Check if already configured by another module
        if not getattr(genai, '_client', None):
            genai.configure(api_key=api_key)
            logging.info("Gemini API configured successfully in text_generation module.")
        else:
            logging.info("Gemini API appears to be already configured.")
        gemini_configured = True
    except Exception as config_err:
        logging.error(f"Failed to configure Gemini API in text_generation: {config_err}")
else:
    logging.warning("GEMINI_API_KEY not found or empty for text_generation module. Quiz generation will fail.")

# Google Custom Search API configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID")
google_search_configured = bool(GOOGLE_API_KEY and GOOGLE_CX_ID)
if not google_search_configured:
    logging.warning("Google Search API not configured (missing GOOGLE_API_KEY or GOOGLE_CX_ID). Text answer generation will fall back to error message.")


# ----------------------------------------------------------------------
# --- Text Answer Generation Function (Uses Google Custom Search) ---
# ----------------------------------------------------------------------
def generate_text_answer(query: str) -> str:
    """
    Fetches top Google Search results and summaries for a given query using the Custom Search API.
    """
    logging.debug(f"generate_text_answer (Google Search) called with query: '{query}'")
    if not google_search_configured:
        logging.error("Google Search API not configured properly.")
        return "Google Search API not configured properly. Check GOOGLE_API_KEY and GOOGLE_CX_ID."

    try:
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX_ID,
            "q": query
        }
        response = requests.get(search_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        results = response.json()
        logging.debug(f"Successfully fetched Google Search results for '{query}'.")

        if "items" not in results or not results["items"]:
            logging.info(f"No results found from Google Search for: '{query}'")
            return "No results found from Google Search."

        # Collect top 3 summaries
        summaries = ["**Top Search Results:**"]
        for item in results["items"][:3]:
            title = item.get("title", "No Title")
            snippet = item.get("snippet", "No Description")
            link = item.get("link", "")
            summaries.append(f"**{title}**\n{snippet}\n🔗 {link}\n")

        return "\n\n".join(summaries)

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error during Google Search for '{query}': {http_err}")
        return f"Error fetching data from Google Search (HTTP Error): {http_err}"
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Network error during Google Search for '{query}': {req_err}")
        return f"Error fetching data from Google Search (Network Error): {req_err}"
    except Exception as e:
        logging.error(f"Unexpected error during Google Search for '{query}': {type(e).__name__} - {e}")
        logging.exception("Traceback for unexpected Google Search error:")
        return f"Error fetching data from Google Search: {e}"


# ----------------------------------------------------------------------
# --- Quiz Generation Function (Uses Gemini) ---
# ----------------------------------------------------------------------
def generate_quiz_json(topic: str, num_questions: int = 5) -> dict:
    """
    Generates a quiz (list of questions and answers) on a given topic using the Gemini API.
    Returns JSON-like dictionary.
    """
    logging.debug(f"generate_quiz_json called with topic: '{topic}'")
    if not gemini_configured:
        logging.error("generate_quiz_json cannot run, Gemini API key not configured.")
        return {"error": "AI service not configured (missing or invalid API key)."}

    try:
        model_name = "models/gemini-2.5-flash"
        model = genai.GenerativeModel(model_name)
        logging.debug(f"Using Gemini model: {model_name}")

        prompt = f"""
        Generate a multiple-choice quiz with exactly {num_questions} questions about the topic: "{topic}".
        For each question, provide:
        1. The question text ('question').
        2. Four options ('options') as a JSON object with keys "A", "B", "C", "D".
        3. The correct answer letter ('answer') which must be one of "A", "B", "C", or "D".

        Return the output ONLY as a single, valid JSON object string. Do not include any introductory text, concluding text, explanations, markdown formatting (like ```json), or anything else outside the JSON structure. The JSON structure must be:
        {{
          "questions": [
            {{
              "question": "...",
              "options": {{ "A": "...", "B": "...", "C": "...", "D": "..." }},
              "answer": "..."
            }}
            // ... (repeat for {num_questions} questions)
          ]
        }}
        """
        logging.debug("Sending prompt to Gemini for quiz generation...")
        generation_config = genai.types.GenerationConfig(temperature=0.7)
        response = model.generate_content(prompt, generation_config=generation_config)

        # Check for empty or blocked response *before* accessing .text
        if not response.parts:
            logging.error("Gemini response was empty or blocked.")
            try:
                feedback = response.prompt_feedback
                reason = getattr(feedback, 'block_reason_message', '') or getattr(feedback, 'block_reason', 'Unknown')
                logging.error(f"Prompt Feedback: {feedback}")
                return {"error": f"Quiz generation blocked by AI. Reason: {reason}"}
            except Exception as feedback_err:
                logging.error(f"Could not retrieve block reason from feedback: {feedback_err}")
                return {"error": "AI response was empty or blocked for an unknown reason."}

        # Proceed only if response has parts
        raw_text = response.text
        logging.debug(f"Raw Gemini response text received:\n{raw_text}")

        # Clean aggressively: remove potential markdown fences and surrounding whitespace
        cleaned_text = raw_text.strip().lstrip('```json').rstrip('```').strip()
        logging.debug(f"Cleaned Gemini response text:\n{cleaned_text}")

        # Attempt to parse the JSON string
        quiz_data = json.loads(cleaned_text)

        # --- Validation ---
        if not isinstance(quiz_data, dict) or "questions" not in quiz_data or not isinstance(quiz_data["questions"], list):
            raise ValueError("Generated JSON root structure ('questions' list) is invalid.")
        if not quiz_data["questions"]:
            raise ValueError("Generated JSON contains an empty 'questions' list.")
        logging.info(f"Generated {len(quiz_data['questions'])} questions.")

        for i, q in enumerate(quiz_data["questions"]):
            q_num = i + 1
            if not isinstance(q, dict) or not all(k in q for k in ["question", "options", "answer"]):
                raise ValueError(f"Question {q_num} is missing required keys ('question', 'options', 'answer').")
            if not isinstance(q["options"], dict) or len(q["options"]) != 4 or not all(opt in q["options"] for opt in "ABCD"):
                raise ValueError(f"Question {q_num} has invalid options structure (must be A, B, C, D).")
            if q["answer"] not in "ABCD":
                raise ValueError(f"Question {q_num} has an invalid answer key: '{q['answer']}' (must be A, B, C, or D).")
            # Ensure options are strings
            for opt_key, opt_val in q["options"].items():
                if not isinstance(opt_val, str):
                    logging.warning(f"Q{q_num} Opt {opt_key} not a string, converting: {opt_val}")
                    q["options"][opt_key] = str(opt_val)

        logging.debug("Quiz JSON validated successfully.")
        return quiz_data

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON from Gemini response: {e}"
        logging.error(error_msg)
        try:
            logging.error(f"--- Raw AI Response Start ---\n{raw_text}\n--- Raw AI Response End ---")
        except NameError:
            logging.error("Raw text was not successfully captured before JSON decode failed.")
        return {"error": f"{error_msg}. Check server logs for the raw response."}
    except ValueError as e:
        error_msg = f"Generated quiz JSON structure validation failed: {e}"
        logging.error(error_msg)
        try:
            logging.error(f"--- Cleaned AI Response Start ---\n{cleaned_text}\n--- Cleaned AI Response End ---")
        except NameError:
            logging.error("Cleaned text was not successfully captured before validation failed.")
        return {"error": f"{error_msg}. Check server logs for the cleaned response."}
    except Exception as e:
        error_msg = f"An unexpected error occurred during quiz generation: {type(e).__name__} - {e}"
        logging.error(error_msg)
        logging.exception("Traceback for unexpected quiz generation error:")
        return {"error": "Unexpected error during quiz generation. Check server logs."}


# ----------------------------------------------------------------------
# --- Complete Notes Generation Function (Uses Gemini) ---
# ----------------------------------------------------------------------
def generate_complete_notes(topic: str) -> dict:
    """
    Generates structured notes, summary, and questions of varying mark values (1, 2, 4, 6, 8, 10).
    """
    logging.debug(f"generate_complete_notes called for topic: '{topic}'")
    if not gemini_configured:
        logging.error("generate_complete_notes cannot run, API key not configured.")
        return {"error": "AI service not configured (missing or invalid API key)."}

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        
        prompt = f"""
        Generate a complete, structured study package for the topic: "{topic}".
        The content MUST be returned as a single, unified text block using standard markdown formatting.

        The package must contain the following sections in order:
        1. **Summary/Conceptual Notes:** A detailed conceptual overview and notes for the topic (H2/## Heading).
        2. **1-Mark Questions (Short Answers):** 5 questions with answers.
        3. **2-Mark Questions (Definitions/Lists):** 3 questions with answers.
        4. **4-Mark Questions (Explanations/Diagrams):** 2 questions with answers.
        5. **6-Mark Questions (In-depth Explanations/Process Steps):** 1 question with answer.
        6. **8-Mark Questions (Comprehensive Analysis/Comparative Study):** 1 question with answer.
        7. **10-Mark Questions (Essay/Detailed Derivation):** 1 question with answer.

        Format Requirements:
        - Use standard Markdown headings (##) for sections.
        - Use ordered lists (1., 2., 3.) for lists and numbered questions.
        - Use bolding (**) for key terms.
        - Questions and Answers must be clearly separated (e.g., using a sub-heading like ### Question and ### Answer).
        - Ensure the content is professional, academic, and ready for a study guide.
        """
        
        logging.debug("Sending prompt to Gemini for structured notes...")
        generation_config = genai.types.GenerationConfig(
            temperature=0.4,
            max_output_tokens=4096
        )
        response = model.generate_content(prompt, generation_config=generation_config)

        if not response.parts:
            logging.error("Gemini response was empty or blocked for structured notes.")
            return {"error": "AI notes generation blocked or returned empty content."}
        
        # Return the raw markdown text and the topic for document naming
        return {
            "title": topic,
            "content_markdown": response.text,
            "success": True
        }

    except Exception as e:
        logging.exception(f"Unexpected error during complete notes generation for '{topic}'")
        return {"error": f"Failed to generate structured notes: {e}"}