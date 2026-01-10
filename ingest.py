from youtube_transcript_api import YouTubeTranscriptApi
from utils import extract_video_id
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

import json
import os


def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

def create_vectorstore(documents, persist_dir="data/vectordb"):
    embedding = get_embedding_model()
    
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory=persist_dir
    )
    
    vectordb.persist()
    return vectordb

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


def load_transcript(video_id):
    path = f"data/transcripts/{video_id}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def chunk_transcript(transcript, video_id, max_words=25):
    chunks = []
    
    current_text = []
    start_time = None
    end_time = None
    word_count = 0

    for entry in transcript:
        text = entry["text"]
        words = text.split()
        
        if start_time is None:
            start_time = entry["start"]

        current_text.append(text)
        word_count += len(words)
        end_time = entry["start"] + entry["duration"]

        if word_count >= max_words:
            chunks.append({
                "text": " ".join(current_text),
                "start_time": start_time,
                "end_time": end_time,
                "video_id": video_id
            })

            # Reset
            current_text = []
            start_time = None
            end_time = None
            word_count = 0

    # Flush remainder
    if current_text:
        chunks.append({
            "text": " ".join(current_text),
            "start_time": start_time,
            "end_time": end_time,
            "video_id": video_id
        })

    return chunks

def save_chunks(video_id, chunks):
    os.makedirs("data/chunks", exist_ok=True)
    path = f"data/chunks/{video_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

def chunks_to_documents(chunks):
    documents = []
    
    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata={
                "video_id": chunk["video_id"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"]
            }
        )
        documents.append(doc)
    
    return documents


if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=aEgSe5pKYj0"
    video_id=extract_video_id(url)
    transcript = fetch_transcript(url)
    save_transcripts(video_id, transcript)
    print("Transcript saved successfully")

    transcript_load = load_transcript(video_id)
    chunks = chunk_transcript(transcript_load, video_id)
    save_chunks(video_id, chunks)
    print(f"Created {len(chunks)} chunks")

    documents = chunks_to_documents(chunks)
    vectordb = create_vectorstore(documents)
    results = vectordb.similarity_search("What is the main topic?", k=3)
    for r in results:
        print(r.metadata, r.page_content[:100])
    print("Vector store created and persisted successfully.")