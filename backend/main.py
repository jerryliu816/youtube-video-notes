import os
import re
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
def load_environment():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    return api_key

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend usage (modify origins if necessary)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; change for production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
LOG_FILE = "fastapi_app.log"
logging.basicConfig(
    filename=LOG_FILE,
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Initialize API Client
try:
    api_key = load_environment()
    groq_client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    logger.error(f"Error initializing API client: {str(e)}")
    raise RuntimeError(f"Error initializing API client: {str(e)}")

# Request Model for Summarization
class SummarizationRequest(BaseModel):
    youtube_url: str
    target_language: str
    mode: str = "video"  # Default mode is 'video'
    user_email: str  # New field to capture user info

# Extract YouTube Video ID
def extract_video_id(youtube_url: str) -> str:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    youtube_url = youtube_url.strip()
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError("Could not extract video ID from URL")

# Get YouTube Transcript
def get_transcript(youtube_url: str):
    try:
        video_id = extract_video_id(youtube_url)
        
        # Load cookies for authentication
        cookies_file = os.getenv('COOKIE_PATH', os.path.join(os.path.dirname(__file__), 'cookies.txt'))
        if not os.path.exists(cookies_file):
            raise HTTPException(status_code=400, detail="Cookie file not found. Please set up authentication.")

        with open(cookies_file, 'r') as f:
            if not f.read().strip():
                raise HTTPException(status_code=400, detail="Cookie file is empty. Please re-export your cookies.")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookies_file)

        try:
            transcript = transcript_list.find_manually_created_transcript()
        except:
            try:
                transcript = next(iter(transcript_list))
            except Exception:
                raise HTTPException(status_code=400, detail="Your YouTube cookies might have expired. Please refresh them.")

        full_transcript = " ".join([part['text'] for part in transcript.fetch()])
        return full_transcript, transcript.language_code

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Summarization Logic with LangChain + Groq API
def summarize_with_groq(transcript: str, language_code: str, model_name: str = "llama-3.1-8b-instant", mode: str = "video"):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=7000, chunk_overlap=1000, length_function=len)
    texts = text_splitter.split_text(transcript)

    intermediate_summaries = []
    
    for i, text_chunk in enumerate(texts):
        system_prompt = f"""You are an expert content summarizer. Create a detailed summary of section {i+1} in {language_code}.
        Maintain important details, arguments, and connections. This summary will later be part of a comprehensive final summary."""

        user_prompt = f"""Summarize the following section:
        - Include key topics, arguments, examples
        - Ensure logical flow and clarity

        Text: {text_chunk}"""

        try:
            response = groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            intermediate_summaries.append(response.choices[0].message.content)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error with Groq API: {str(e)}")

    combined_summary = "\n\n=== Next Section ===\n\n".join(intermediate_summaries)
    
    final_system_prompt = f"""You are an expert summarizer. Create a well-structured summary in {language_code} 
    from the provided intermediate summaries, ensuring logical connections."""

    final_user_prompt = f"""Summarize comprehensively:
    - Keep key points and logical flow
    - Make it understandable for someone unfamiliar with the content
    - Highlight any action items

    Intermediate summaries:
    {combined_summary}"""

    try:
        final_response = groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": final_user_prompt}
            ],
            temperature=0.7,
            max_tokens=8000
        )
        return final_response.choices[0].message.content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with Groq API: {str(e)}")

# Middleware to Log Requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# API Route: Summarize YouTube Video
@app.post("/summarize/")
async def summarize_video(request: SummarizationRequest):
    logger.info(f"User '{request.user_email}' requested summary for {request.youtube_url}")
    try:
        transcript, language_code = get_transcript(request.youtube_url)
        summary = summarize_with_groq(transcript, request.target_language, mode=request.mode)
        logger.info(f"Successfully summarized video for user '{request.user_email}'")
        return {"summary": summary, "language": request.target_language}
    except Exception as e:
        logger.error(f"Error summarizing video: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Root Route
@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    return {"message": "FastAPI YouTube Summarizer is running!"}
