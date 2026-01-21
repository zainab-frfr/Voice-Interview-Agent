import time, os, uuid, httpx, csv
from deepgram import DeepgramClient
# from deepgram.listen.v1.media import PrerecordedOptions
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize Deepgram and supabase clients, and eleven labs constants 
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
dg_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "90ipbRoKi4CpHXvKVtl0"
ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

async def transcribe_with_deepgram(audio_data: bytes):
    """Action 1: Transcribe Urdu audio using Deepgram."""
    start_time = time.time()
    response = dg_client.listen.v1.media.transcribe_file(
        request=audio_data,
        model="whisper-large",
        language="ur",
        smart_format=True
    )
    transcription_time = time.time() - start_time
    
    # Debug: Check response structure
    if not response.results or not response.results.channels:
        raise ValueError(f"No channels in response: {response}")
    
    if not response.results.channels[0].alternatives:
        raise ValueError(f"No alternatives in channel: {response.results.channels[0]}")
    
    text = response.results.channels[0].alternatives[0].transcript
    
    # text = response.results.channels[0].alternatives[0].transcript
    
    return text, transcription_time

async def upload_audio_to_supabase(session_id: str, question_id: str, audio_data: bytes):
    """Action 2: Upload raw audio to Supabase Storage and get public URL."""
    storage_path = f"interviews/{session_id}/{question_id}_{uuid.uuid4()}.wav"
    
    supabase.storage.from_("interview-audio").upload(
        storage_path, audio_data, 
        file_options={"content-type": "audio/wav"}
    )
    
    return supabase.storage.from_("interview-audio").get_public_url(storage_path)

async def save_metadata_to_db(response_data: dict):
    """Action 3: Log the transcription and file URL into the database."""
    return supabase.table('interview_responses').insert(response_data).execute()


async def call_elevenlabs_api(text: str):
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        "model_id": "eleven_multilingual_v2",
    }
    
    # We use an async client
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ELEVEN_TTS_URL}/{VOICE_ID}",
            headers=headers,
            json=payload,
            timeout=30.0
        )
    return response


async def create_interview_session(session_id: str, total_questions: int):
    interview_data = {
        "session_id": session_id,
        "total_questions": total_questions,
        "status": "in_progress"
    }
    return supabase.table('interviews').insert(interview_data).execute()

async def update_interview_status(session_id: str):
    update_data = {
        "completed_at": datetime.now().isoformat(),
        "status": "completed"
    }
    return supabase.table('interviews').update(update_data).eq('session_id', session_id).execute()

async def fetch_full_interview_data(session_id: str):
    interview = supabase.table('interviews').select("*").eq('session_id', session_id).execute()
    responses = supabase.table('interview_responses').select("*").eq('session_id', session_id).order('response_order').execute()
    return interview, responses

def create_csv_file(session_id: str, interview_data: list, responses_data: list):
    """Helper to handle the file writing logic"""
    os.makedirs("results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"interview_{session_id}_{timestamp}.csv"
    filepath = os.path.join("results", filename)
    
    total_time = sum(r['transcription_time'] for r in responses_data)

    with open(filepath, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        # Header Info
        writer.writerow(["Session ID", session_id])
        writer.writerow(["Started At", interview_data[0]['started_at'] if interview_data else ""])
        writer.writerow(["Completed At", interview_data[0]['completed_at'] if interview_data else ""])
        writer.writerow([])
        # Data Columns
        writer.writerow(["Order", "Question ID", "Type", "Question", "Answer", "Time (s)", "Timestamp", "Audio URL"])
        for r in responses_data:
            writer.writerow([
                r['response_order'], r['question_id'], r['question_type'],
                r['question_text'], r['answer_text'], r['transcription_time'],
                r['timestamp'], r['audio_file_url']
            ])
        writer.writerow([])
        writer.writerow(["Total Transcription Time", f"{total_time:.2f} seconds"])
        
    return filepath, filename