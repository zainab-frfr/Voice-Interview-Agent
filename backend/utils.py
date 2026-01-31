import time, os, uuid, httpx, csv, io, json
from deepgram import DeepgramClient
# from deepgram.listen.v1.media import PrerecordedOptions
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv
import whisper
import torch, re
import tempfile
from groq import Groq

# Load the model globally to avoid reloading on every request
# 'large-v3' is the current state-of-the-art for local Whisper
# device = "cuda" if torch.cuda.is_available() else "cpu"
# model = whisper.load_model("large-v3", device=device)

# The URL where your Backend 2 is hosted
WHISPER_SERVER_URL = "https://your-backend-2-url.com/transcribe"

load_dotenv()

# llm_client initialization
llm_client = Groq(api_key= os.getenv("GROQ_API_KEY"))

# Initialize Deepgram and supabase clients, and eleven labs constants 
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
dg_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "XrExE9yKIg1WjnnlVkGX" #"90ipbRoKi4CpHXvKVtl0"
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

async def transcribe_with_whisper(audio_data: bytes):
    """
    Action 1: Send audio to Backend 2 for Whisper transcription.
    """
    try:
        # We use a long timeout because Whisper Large-v3 takes time to process
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Prepare the file for the multipart/form-data request
            files = {'file': ('audio.wav', audio_data, 'audio/wav')}
            
            response = await client.post(WHISPER_SERVER_URL, files=files)
            
            if response.status_code != 200:
                print(f"Transcription Server Error: {response.text}")
                return "Transcription failed", 0.0
            
            data = response.json()
            # Extract text and time from Backend 2's response
            return data.get("text", ""), data.get("transcription_time", 0.0)

    except Exception as e:
        print(f"Error calling Backend 2: {e}")
        return f"Error: {str(e)}", 0.0


def validate_answer(question, answer):
    """
    Sends the question + user answer to Groq for validation.
    Returns:
      - valid: True/False
      - category: response type
      - message: guidance / explanation if needed
      - api_time: time taken for API call in seconds
    """

    prompt = f"""
You are an assistant that validates user responses to interview questions in Urdu.

IMPORTANT LANGUAGE RULES:
- NEVER use the phrase "براہِ کرم".
- ALWAYS use "برائے مہربانی" instead.
- you are a female interviewer so use FEMININE PRONOUNS WHERE NEEDED.
- Maintain a polite, respectful, and neutral Urdu tone.
- Respond in **URDU** only 
- the answer might contain spelling mistakes (for eg. "ساتھ" instead of "سات") so take that into account while classifying.

Question: "{question}"
Answer: "{answer}"

TASK:
Classify the user's answer into ONE category:

- valid (directly answers the question)
- irrelevant
- evasive
- abusive
- repeat (asking to repeat OR explain the question)
- refusal (wants to stop or end the interview)

SPECIAL RULES:

1. VALID:
- valid = true
- message must be an empty string

2. REPEAT:
- Includes requests like:
  "سوال دہرا دیں", "سوال سمجھ نہیں آیا", "کیا وضاحت کر سکتے ہیں"
- Do NOT scold the user.
- Apologize politely.
- Briefly explain the question in simple Urdu.
- Imply the question may not have been conveyed clearly.

3. REFUSAL:
- User wants to end the interview.
- Respond politely and accept the request.
- Do NOT ask them to answer again.

4. OTHER INVALID TYPES:
- Politely guide the user on how to answer.
- Use "برائے مہربانی".

OUTPUT:
Return ONLY valid JSON in exactly this format:

{{
  "valid": true/false,
  "category": "valid | irrelevant | evasive | abusive | repeat | refusal",
  "message": "appropriate Urdu message or empty string"
}}
"""

    # # Start timing
    # start_time = time.time()

    response = llm_client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768"
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    # End timing
    # end_time = time.time()
    # api_time = end_time - start_time

    try:
        output_text = response.choices[0].message.content.strip()
        result = json.loads(output_text)
        # result["api_time"] = api_time  # Add timing to result
    except Exception:
        result = {
            "valid": False,
            "category": "error",
            "message": "برائے مہربانی دھرائیں  سسٹم جواب کو سمجھ نہیں سکا۔",
            # "api_time": api_time
        }

    return result

def get_sentiment_response(answer):
    """
    Function to ask a question and determine sentiment based on numeric response.

    Args:
        question (str): The question to ask the respondent

    Returns:
        str: Either "dislike" or "like" based on the numeric response
    """

    # Mapping of Urdu number words to digits
    urdu_numbers = {
        'ایک': '1', 'ek': '1',
        'دو': '2', 'do': '2',
        'تین': '3', 'teen': '3',
        'چار': '4', 'char': '4', 'chaar': '4',
        'پانچ': '5', 'panch': '5', 'paanch': '5',
        'چھ': '6', 'chhe': '6', 'chhay': '6',
        'سات': '7', 'saat': '7', 'ساتھ': '7',
        'آٹھ': '8', 'aath': '8',
        'نو': '9', 'nau': '9', 'no': '9'
    }

    # Urdu digits to English digits mapping
    urdu_digits = {
        '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5',
        '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }

    while True:
        # the response from the user
        response = answer.strip()

        # Convert Urdu digits to English digits
        for urdu_digit, english_digit in urdu_digits.items():
            response = response.replace(urdu_digit, english_digit)

        # Replace Urdu number words with English digits
        response_lower = response.lower()
        for urdu_word, digit in urdu_numbers.items():
            response_lower = response_lower.replace(urdu_word, digit)

        # Extract numeric value from response (1-9)
        numbers = re.findall(r'\b[1-9]\b', response_lower)
        print(numbers)

        if numbers:
            # Get the first valid number found
            number = int(numbers[0])
            print(number)

            # Check if number is in valid range (1-9)
            if 1 <= number <= 9:
                if 1 <= number <= 4:
                    return "dislike"
                else:  # 5 to 9
                    return "like"

        # If no valid number found, ask again
        return "invalid"


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