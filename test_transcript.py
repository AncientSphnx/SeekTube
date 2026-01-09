from youtube_transcript_api import YouTubeTranscriptApi

video_id = "aEgSe5pKYj0"
#video_id = video_url.split("v=")[1]

# Try the correct method name for older versions
api= YouTubeTranscriptApi()
transcript = api.fetch(video_id)

print(transcript[:3])