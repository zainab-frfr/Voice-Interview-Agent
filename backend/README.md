# 🎙️ Voice Interview Agent - Backend

This is the Python-based brain of the Voice Interview Agent. It uses **FastAPI** for the web server, **Deepgram** for Urdu transcription, **ElevenLabs** for voice synthesis, and **Supabase** for data and audio storage.

--- 

## 🏗️ Architecture: The "Ear-Brain-Mouth" Pipeline

The backend handles the heavy lifting of processing audio and managing data through a three-step pipeline:

1.  **Speech-to-Text (STT):** Receives `.wav` files from the frontend and uses **Deepgram (Whisper Large)** with specific Urdu (`ur`) language settings to ensure high transcription accuracy.
2.  **Parallel Storage:** Uses `asyncio.gather` to simultaneously upload raw audio to **Supabase Storage** and log metadata/transcripts into the `interview_responses` table.
3.  **Voice Synthesis (TTS):** Uses **ElevenLabs (Multilingual V2)** to convert survey questions into natural-sounding Urdu audio, which is then streamed back to the frontend.

---

## 🚀 Getting Started

### 1. Environment Setup
Create a `.env` file in the `backend/` directory:

```bash
DEEPGRAM_API_KEY=your_deepgram_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_API_KEY=your_supabase_anon_key
ELEVENLABS_API_KEY=your_elevenlabs_key

```

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload

```

*The server will be available at `http://127.0.0.1:8000`.*

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| **GET** | `/get-questions` | Returns the list of 24 Urdu questions from `survey_data.py`. |
| **POST** | `/start-interview` | Initializes a new session in the `interviews` table. |
| **POST** | `/stt` | Transcribes audio, uploads to storage, and saves to DB. |
| **POST** | `/tts` | Converts text to speech and streams back audio bytes. |
| **POST** | `/complete-interview/{id}` | Marks a session as `completed` with a timestamp. |
| **GET** | `/get-interview/{id}` | Fetches all transcripts and metadata for a session. |
| **POST** | `/generate-csv/{id}` | Generates a downloadable CSV report of the interview. |

---

## 📂 Project Structure

* **`main.py`**: The entry point. Handles API routing, middleware (CORS), and request validation.
* **`utils.py`**: Integration logic for Deepgram, ElevenLabs, and Supabase.
* **`survey_data.py`**: Centralized storage for the 10 screening and 14 main interview questions.
* **`results/`**: (Auto-generated) Directory where generated CSV reports are stored.

---

## ⚠️ Important Implementation Notes

* **Urdu Support:** Transcription is optimized using the `whisper-large` model for the `ur` language code.
* **Performance:** The `/stt` endpoint uses asynchronous processing to ensure audio uploads don't block the transcription return.
* **CSV Encoding:** Reports are exported with `utf-8-sig` encoding to ensure Urdu script displays correctly in Microsoft Excel.
