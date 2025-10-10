from yt_dlp import YoutubeDL

def find_top_videos(query, max_results=3):
    """
    Search YouTube for the top N educational videos for a given topic.
    Returns a list of dictionaries: [{'title': ..., 'watch_url': ...}, ...]
    """
    search_query = f"{query} educational tutorial"

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': 'in_playlist',
        'noplaylist': True,
        'default_search': f'ytsearch{max_results}'  # top N results
    }

    videos = []

    with YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(search_query, download=False)
            if 'entries' in result and len(result['entries']) > 0:
                for entry in result['entries']:
                    title = entry.get('title')
                    video_id = entry.get('id')
                    if title and video_id:
                        watch_url = f"https://www.youtube.com/watch?v={video_id}"
                        videos.append({"title": title, "watch_url": watch_url})
            return videos
        except Exception as e:
            print(f"⚠️ Error fetching videos: {e}")
            return []
