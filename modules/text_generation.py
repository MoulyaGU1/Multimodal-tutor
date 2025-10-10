import wikipediaapi

def generate_text_answer(query):
    """
    Generates a detailed summary of any topic using the Wikipedia-API.
    This provides dynamic content for any user query.
    """
    try:
        # Create a Wikipedia API object with a user-agent (good practice)
        wiki_wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='MultimodalTutor/1.0'
        )
        
        print(f"Searching Wikipedia for: {query}")
        
        # Get the page object for the user's query
        page = wiki_wiki.page(query)

        if not page.exists():
            print(f"Wikipedia page not found for: {query}")
            return f"Sorry, I could not find a Wikipedia page for '{query}'. Please try a different search term."

        # Return the first few paragraphs of the summary for a detailed yet concise explanation.
        # The summary is split by newlines, and we take the first 3 paragraphs.
        summary_paragraphs = page.summary.split('\n')
        detailed_summary = "\n\n".join(summary_paragraphs[:3])

        return detailed_summary

    except Exception as e:
        print(f"An unknown error occurred while searching Wikipedia: {e}")
        return "Sorry, an unexpected error occurred while trying to find information on this topic."