from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio, io
from pydantic import BaseModel
from utils import *
from survey_data import QUESTIONS # the questions 
from urllib.parse import unquote
import io, re
import edge_tts
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from gtts import gTTS

# load_dotenv()

app = FastAPI() # initializes the actual web application that uvicorn will run

# ------------------ Middleware & Clients ------------------
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], # allows requests from all origins
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)


class InterviewStart(BaseModel):
    session_id: str
    

@app.get("/")
def read_root():
    return {
        "message": "Urdu Interview API is running",
        "total_questions": len(QUESTIONS),
        "endpoints": [
            "/get-questions",
            "/start-interview",
            "/tts",
            "/stt",
            "/complete-interview",
            "/get-interview/{session_id}",
            "/generate-csv/{session_id}"
        ]
    }

@app.get("/get-questions")
def get_questions():
    """Get all interview questions"""
    return {"questions": QUESTIONS, "total": len(QUESTIONS)}


@app.post("/stt")
async def transcribe_audio(
    file: UploadFile = File(...),
    session_id: str = "",
    question_id: str = "",
    question_text: str = "",
    question_type: str = "",
    response_order: int = 0
):
    if not session_id or not question_id:
        raise HTTPException(status_code=400, detail="Missing IDs")

    try:
        # 0. Read audio data
        audio_data = await file.read()

        # Start both tasks at the exact same time
        # This returns a list: [ (text, duration), file_url ]
        results = await asyncio.gather(
            transcribe_with_deepgram(audio_data),
            upload_audio_to_supabase(session_id, question_id, audio_data)
        )

        # Unpack the results
        (text, duration) = results[0]
        file_url = results[1]
        
        print(text)
        
        json_groq_response = validate_answer(question=question_text, answer=text)
        if json_groq_response.get("category") == "valid":
            if question_type == "follow-up":
                sentiment = get_sentiment_response(answer=text)
                if sentiment == "like":
                    next_qes_id = int(question_id) + 2
                elif sentiment == "dislike":
                    next_qes_id = int(question_id) + 1
                else:
                    next_qes_id = int(question_id) 
                    json_groq_response["message"] = "براہِ مہربانی 1 سے 9 کے درمیان نمبر بولیں۔"
            else:
                next_qes_id = int(question_id) + 1
        elif json_groq_response.get("category") == "refusal": # end interview 
            next_qes_id = int(question_id)
        else: # stay on current qs, ask message 
            next_qes_id = int(question_id)
            
        # Now that we have both the text and the URL, save to DB
        response_payload = {
            "session_id": session_id,
            "question_id": question_id,
            "question_text": question_text,
            "question_type": question_type,
            "answer_text": text,
            "transcription_time": round(duration, 2),
            "audio_file_url": file_url,
            "response_order": response_order,
        }
        await save_metadata_to_db(response_payload)
        
        
            # "next_qes_id": next_qes_id,
            # "message": json_groq_response.get("message", "")
        response_payload["next_qes_id"] = next_qes_id
        response_payload["message"] = json_groq_response.get("message", "")

        return {"success": True, **response_payload}

    except Exception as e:
        print(f"Error in STT Endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts")
async def generate_tts(text: str = Query(...)):
    if not text:
        raise HTTPException(status_code=400, detail="Text required")

    # Try Edge-TTS first
    try:
        voice = "ur-PK-UzmaNeural"
        communicate = edge_tts.Communicate(text, voice)
        
        # Collect audio in buffer
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if not audio_data:
            raise Exception("No audio data generated from Edge-TTS")

        print(f"Edge-TTS Success: {len(audio_data)} bytes")
        audio_stream = io.BytesIO(audio_data)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        print(f"Edge-TTS failed: {e}. Falling back to gTTS...")
        
        # Fallback to gTTS
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang='ur', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            print(f"gTTS Success: {len(audio_buffer.getvalue())} bytes")
            return StreamingResponse(audio_buffer, media_type="audio/mpeg")

        except Exception as gtts_error:
            print(f"gTTS also failed: {gtts_error}")
            raise HTTPException(status_code=500, detail=f"Both TTS services failed: {str(gtts_error)}")
    
# @app.post("/tts")
# async def generate_tts(text: str = Query(...)):
#     if not text:
#         raise HTTPException(status_code=400, detail="Text required")

#     try:
#         # 'ur-PK-UzmaNeural' is a very clear, natural female Urdu voice
#         # 'ur-PK-AsadNeural' is the male version
#         voice = "ur-PK-UzmaNeural"
        
#         communicate = edge_tts.Communicate(text, voice)
        
#         # We collect the audio in an internal buffer
#         audio_data = b""
#         async for chunk in communicate.stream():
#             if chunk["type"] == "audio":
#                 audio_data += chunk["data"]

#         if not audio_data:
#             raise Exception("No audio data generated")

#         audio_stream = io.BytesIO(audio_data)
#         return StreamingResponse(audio_stream, media_type="audio/mpeg")

#     except Exception as e:
#         print(f"Edge-TTS Error: {e}")
#         raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
    
@app.post("/start-interview")
async def start_interview(data: InterviewStart):
    try:
        await create_interview_session(data.session_id, len(QUESTIONS))
        
        return {
            "success": True,
            "session_id": data.session_id,
            "total_questions": len(QUESTIONS),
            "message": "Interview session created"
        }
    except Exception as e:
        print(f"❌ Error starting interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")
    
    
@app.post("/complete-interview/{session_id}")
async def complete_interview(session_id: str):
    """Mark interview as completed using helper function"""
    try:
        # Call the helper
        result = await update_interview_status(session_id)
        
        # Check if the update actually found a record
        if not result.data:
            raise HTTPException(status_code=404, detail="Session ID not found")
            
        return {"success": True, "message": "Interview completed successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Update Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update interview status")
    

@app.get("/get-interview/{session_id}")
async def get_interview(session_id: str):
    """Retrieve full summary of interview session"""
    try:
        # Call the helper
        interview, responses = await fetch_full_interview_data(session_id)

        if not interview.data:
            raise HTTPException(status_code=404, detail="Interview session not found")

        return {
            "interview": interview.data[0],
            "responses": responses.data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Retrieval Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interview data")
    
    
@app.post("/generate-csv/{session_id}")
async def generate_csv_for_session(session_id: str):
    try:
        # Re-use our fetch helper from the previous part!
        interview, responses = await fetch_full_interview_data(session_id)

        if not responses.data:
            raise HTTPException(status_code=404, detail="No responses found for this session")

        # Generate the physical file
        filepath, filename = create_csv_file(session_id, interview.data, responses.data)

        return FileResponse(filepath, media_type="text/csv", filename=filename)

    except Exception as e:
        print(f"CSV Error: {e}")
        raise HTTPException(status_code=500, detail="CSV generation failed")
    
    
# @app.post("/tts")
# async def generate_tts(text: str = Query(...)):
#     if not text:
#         raise HTTPException(status_code=400, detail="Text required")

#     try:
#         response = await call_elevenlabs_api(text)
        
#         if response.status_code != 200:
#              raise HTTPException(status_code=response.status_code, detail="ElevenLabs Error")

#         # streaming directly from memory
#         audio_stream = io.BytesIO(response.content)

#         return StreamingResponse(audio_stream, media_type="audio/mpeg")

#     except Exception as e:
#         print(f"TTS Error: {e}")
#         raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
