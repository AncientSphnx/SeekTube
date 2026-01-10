from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qa import ask_question
from ingest import extract_video_id, fetch_transcript, save_transcripts, chunk_transcript, chunks_to_documents, create_vectorstore
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="YouTube Knowledge Base API")

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

class QuestionRequest(BaseModel):
    question: str
    video_id: str

class ProcessRequest(BaseModel):
    url: str

@app.post("/process")
def process_video(req: ProcessRequest):
    print(f"Received request to process: {req.url}")
    try:
        # Extract video ID
        video_id = extract_video_id(req.url)
        print(f"Extracted video ID: {video_id}")
        
        # Create video-specific directory
        persist_dir = f"data/vectordb/video_{video_id}"
        
        # Check if already processed
        if os.path.exists(persist_dir):
            print(f"Video {video_id} already processed")
            return {"video_id": video_id, "status": "already_processed"}
        
        # Fetch and save transcript
        try:
            transcript = fetch_transcript(req.url)
            print(f"Successfully fetched transcript with {len(transcript)} segments")
        except RuntimeError as e:
            if "Subtitles are disabled for this video" in str(e):
                raise HTTPException(
                    status_code=400, 
                    detail="This video doesn't have available subtitles. Please try a different YouTube video that has captions/transcripts enabled."
                )
            else:
                raise HTTPException(status_code=400, detail=f"Failed to fetch transcript: {str(e)}")
        
        save_transcripts(video_id, transcript)
        
        # Load transcript and create chunks
        from ingest import load_transcript
        transcript_data = load_transcript(video_id)
        chunks = chunk_transcript(transcript_data, video_id)
        print(f"Created {len(chunks)} chunks")
        
        # Create documents and vector store
        documents = chunks_to_documents(chunks)
        vectordb = create_vectorstore(documents, persist_dir)
        print(f"Created vector store at {persist_dir}")
        
        return {"video_id": video_id, "status": "processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")

@app.post("/ask")
def ask(req: QuestionRequest):
    try:
        response = ask_question(req.question, req.video_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)