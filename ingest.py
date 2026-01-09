from youtube_transcript_api import YouTubeTranscriptApi
from utils import extract_video_id
import json
import os


def fetch_transcript(youtube_url):
    video_id = extract_video_id(youtube_url)
    
    try:
        api= YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        return transcript
    except Exception as e:
        raise RuntimeError(f"Transcript not available: {e}")

def save_transcripts(video_id,transcript):
    os.makedirs("data/transcripts", exist_ok=True)

    transcript_data = []
    for snippet in transcript:
        transcript_data.append({
            'text': snippet.text,
            'start': snippet.start,
            'duration': snippet.duration
        })
    
    path = f"data/transcripts/{video_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, indent=2)

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=aEgSe5pKYj0"
    video_id=extract_video_id(url)
    transcript = fetch_transcript(url)
    save_transcripts(video_id, transcript)
    print("Transcript saved successfully")