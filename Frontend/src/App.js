import React, { useState } from 'react';
import './App.css';
import { Search, Play, Loader2, ExternalLink, Link, Youtube } from 'lucide-react';
import axios from 'axios';

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [videoId, setVideoId] = useState(null);
  const [answer, setAnswer] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processed, setProcessed] = useState(false);

  const handleProcessVideo = async (e) => {
    e.preventDefault();
    if (!youtubeUrl.trim()) return;

    setProcessing(true);
    setError(null);

    try {
      const response = await axios.post('https://seektube.onrender.com/process', {
        url: youtubeUrl.trim()
      });
      
      setVideoId(response.data.video_id);
      setProcessed(true);
      
      if (response.data.status === 'already_processed') {
        console.log('Video was already processed');
      }
    } catch (err) {
      console.error('Full error object:', err);
      console.error('Error response:', err.response);
      console.error('Error data:', err.response?.data);
      console.error('Error status:', err.response?.status);
      
      if (err.response?.data?.detail?.includes("subtitles")) {
        setError('This video doesn\'t have available subtitles. Please try a different YouTube video that has captions/transcripts enabled.');
      } else if (err.response?.data?.detail) {
        setError(`Backend error: ${err.response.data.detail}`);
      } else {
        setError(`Failed to process video. ${err.message || 'Please check the URL and try again.'}`);
      }
    } finally {
      setProcessing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || !videoId) return;

    setLoading(true);
    setError(null);
    setAnswer(null);

    try {
      const response = await axios.post('https://seektube.onrender.com/ask', {
        question: question.trim(),
        video_id: videoId
      });
      
      setAnswer(response.data);
    } catch (err) {
      setError('Failed to get response. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const extractVideoTitle = (url) => {
    const videoId = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
    return videoId ? `Video ${videoId[1]}` : 'YouTube Video';
  };

  return (
    <div className="app">
      <header className="header">
        <h1 className="title">YouTube Video Knowledge Base</h1>
        <p className="subtitle">Ask questions. Jump to answers. Save hours.</p>
      </header>

      <main className="main">
        {/* Video Processing Section */}
        {!processed && (
          <div className="question-card">
            <form onSubmit={handleProcessVideo} className="question-form">
              <div className="input-container">
                <Link className="search-icon" size={20} />
                <input
                  type="text"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="Paste YouTube URL here…"
                  className="question-input"
                  disabled={processing}
                />
              </div>
              <button
                type="submit"
                disabled={processing || !youtubeUrl.trim()}
                className="ask-button"
              >
                {processing ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    Processing Video…
                  </>
                ) : (
                  <>
                    <Youtube size={16} />
                    Process Video
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Video Status */}
        {processed && videoId && (
          <div className="status-card">
            <div className="status-content">
              <Youtube className="status-icon" size={20} />
              <div>
                <h3>Video Ready</h3>
                <p>Video ID: {videoId}</p>
                <p>Now you can ask questions about this video</p>
              </div>
              <button 
                onClick={() => {
                  setProcessed(false);
                  setVideoId(null);
                  setAnswer(null);
                  setYoutubeUrl('');
                }}
                className="reset-button"
              >
                Process New Video
              </button>
            </div>
          </div>
        )}

        {/* Question Section */}
        {processed && (
          <div className="question-card">
            <form onSubmit={handleSubmit} className="question-form">
              <div className="input-container">
                <Search className="search-icon" size={20} />
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about the video…"
                  className="question-input"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="ask-button"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    Thinking…
                  </>
                ) : (
                  'Ask AI'
                )}
              </button>
            </form>
          </div>
        )}

        {error && (
          <div className="error-card">
            <p>{error}</p>
          </div>
        )}

        {answer && (
          <div className="results-section">
            <div className="answer-card">
              <h2 className="section-title">Answer</h2>
              <p className="answer-text">
                {answer.answer === "The video does not mention this." ? (
                  <span className="not-found">The video does not mention this.</span>
                ) : (
                  answer.answer
                )}
              </p>
            </div>

            {answer.timestamps && answer.timestamps.length > 0 && (
              <div className="sources-card">
                <h2 className="section-title">Sources</h2>
                <div className="timestamps-list">
                  {answer.timestamps.map((timestamp, index) => (
                    <a
                      key={index}
                      href={timestamp.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="timestamp-item"
                    >
                      <Play size={16} />
                      <span className="time">{formatTime(timestamp.start_time)}</span>
                      <ExternalLink size={14} />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
