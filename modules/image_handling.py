import requests

# Replace with your Unsplash API key
UNSPLASH_ACCESS_KEY = "5j4babDLm1ITLoHaARc5xMFIu1WxZufsuvBJqeq2t2o"

def find_relevant_images(query, max_results=3):
    """
    Fetch top relevant images for a query using Unsplash API.
    Returns a list of image URLs.
    """
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": max_results,
        "client_id": UNSPLASH_ACCESS_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        images = []
        for item in data.get("results", []):
            image_url = item.get("urls", {}).get("regular")
            if image_url:
                images.append(image_url)

        return images

    except Exception as e:
        print(f"⚠️ Error fetching images from Unsplash: {e}")
        return []
