import logging
import json
import os
import asyncio
from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, llm
from livekit.plugins import groq, deepgram,  azure, silero
from supabase import create_client, Client


load_dotenv(".env.local")
logger = logging.getLogger("insight-ai")
server = AgentServer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Keywords for each question to help with matching
QUESTION_KEYWORDS = {
    "1": ["جینڈر", "مرد", "عورت", "gender"],
    "2": ["عمر", "age", "سال"],
    "3": ["ریو", "دیکھنے", "visual", "look", "appeal", "7", "1"],
    "4": ["ذائقہ", "taste", "کس حد", "7"],
    "5": ["مجموعی", "overall", "9", "طور"],
    "6": ["پسند نہیں", "تفصیل", "وجہ", "why", "not like"],
    "7": ["روپے", "30", "خریدیں", "buy"],
    "8": ["کچھ اور", "مشورہ", "suggestion", "anything else"]
}
 
# 1. Your Structured Questionnaire
QUESTIONS = [
    {"id": "1", "text": "آپ کا جینڈر کیا ہے؟ مرد یا عورت", "type": "general"},
    {"id": "2", "text": "اپنی عمر بتائیں۔", "type": "general"},
    {"id": "3", "text": "آپ کو ریو بسکٹ دیکھنے میں کیسا لگا؟ 1 سے 7 کے اسکیل پر بتائیں، جہاں 1 کا مطلب ہے 'بالکل بھی پسند نہیں آیا' اور 7 کا مطلب ہے 'بہت پسند آیا'۔", "type": "general"},
    {"id": "4", "text": "برائے مہربانی بتائیں کہ آپ کو ریو کا ذائقہ کس حد تک پسند آیا؟ 1 سے 7 کے اسکیل پر جہاں 1 کا مطلب ہے بالکل بھی پسند نہیں آیا اور 7 کا مطلب ہے بہت پسند آیا۔", "type": "general"},
    {"id": "5", "text": "مجموعی طور پر آپ کو ریو کیسا لگا؟ 1 سے 9 کے اسکیل پر بتائیں، جہاں 1 کا مطلب ہے 'بالکل بھی پسند نہیں آیا' اور 9 کا مطلب ہے 'بہت پسند آیا'۔", "type": "general"},
    {"id": "6", "text": "آپ کے جواب سے لگتا ہے آپ کو ریو نہیں پسند آیا۔ برائے مہربانی تفصیل سے بتائیں کیوں پسند نہیں آیا؟", "type": "conditional"},
    {"id": "7", "text": "اگر ریو بسکٹ کے 2 بسکٹ کا پیک 30 روپے میں دستیاب ہو، تو کیا آپ اسے خریدیں گے؟ 1، جی ہاں خریدوں گا، 2، نہیں خریدوں گا، 3، شاید یا کچھ کہہ نہیں سکتا۔", "type": "general"},
    {"id": "8", "text": "کیا آپ ریو کے بارے میں کچھ اور کہنا چاہیں گے یا کوئی مشورہ دینا چاہیں گے؟", "type": "general"}
]

def detect_question_id(transcript: str) -> dict:
    
    best_match = None
    best_score = 0
    
    transcript_lower = transcript.lower()
    
    for q_id, keywords in QUESTION_KEYWORDS.items():
        keyword_matches = sum(1 for kw in keywords if kw in transcript_lower)
        
        if keyword_matches > 0:
            score = keyword_matches
            if score > best_score:
                best_score = score
                best_match = next((q for q in QUESTIONS if q["id"] == q_id), None)
            
    return best_match

async def save_response_to_supabase(session_id: str, question_id: str, question_text: str, response: str):
    """
    Save interview response to Supabase.
    Stores all responses as-is.
    """
    try:
        data = {
            "session_id": session_id,
            "question_id": question_id,
            "question": question_text,
            "response": response,
        }
        
        result = supabase.table("live_responses").insert(data).execute()
        logger.info(f"Saved response to Supabase: Q{question_id} for session {session_id}")
        return result
    
    except Exception as e:
        logger.error(f"Error saving to Supabase: {str(e)}")
        return None
    
class InsightAIAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=f"""
            You are an expert market research assistant. Your name is **"InsightAI."**

Your objective is to complete this interview to gather insights about Rio biscuit. Please ask the following questions in order:

**Questions:**
{json.dumps(QUESTIONS, ensure_ascii=False)}

**Strict Rules (Logic Rules):**

1. Always speak in Urdu.
2. Ask only one question at a time.
3. Listen carefully and understand the user’s responses, then ask the next question.
4. When asking questions, try to pronounce every word clearly and correctly.
5. Branching logic after Question 5:

   * If the user’s answer is between 1 and 4, you must ask Question 6 (ask for the reason).
   * If the answer is 5 or above, skip Question 6 and ask Question 7.
6. When all questions are completed, say "Thank you" and end the interview.
7. Never repeat user's response back to them. 
8. Do not repeat a question unless respondent asks for clarity. 
9. Be conversational, clear, and concise. 

Always wait for the user’s response and then ask the next question according to the logic.

            """
        )

@server.rtc_session()
async def my_agent(ctx: JobContext):
    session_id = ctx.job.id
    
    logger.info(f"Starting InsightAI session {session_id} for room: {ctx.room.name}")

    session = AgentSession(
        stt=deepgram.STT(language="ur"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=azure.TTS(voice="ur-PK-UzmaNeural"),
        vad= silero.VAD.load()
    )   
    
    current_question = None 
    last_saved_response = None
    
    QUESTION_MARKERS = {
        "1": "جینڈر",
        "2": "عمر",
        "3": "دیکھنے میں کیسا",
        "4": "ذائقہ",
        "5": "مجموعی طور",
        "6": "پسند نہیں",
        "7": "روپے",
        "8": "کچھ اور"
    }

    # Observability: Print the conversation flow in the console
    @session.on("user_input_transcribed")
    def on_user_input(event):
        
        if not event.is_final:
            return
        
        transcript = event.transcript
        logger.info(f"User: {transcript}")
        
        nonlocal current_question, last_saved_response
        
        if current_question and last_saved_response != transcript:
            asyncio.create_task(
                save_response_to_supabase(
                    session_id,
                    current_question["id"],
                    current_question["text"],
                    transcript
                )
            )
            last_saved_response = transcript

    @session.on("conversation_item_added")
    def on_conversation_item(event):
        if event.item.role == "assistant":
            transcript = event.item.text_content.lower()
            
            nonlocal current_question
            
            for q_id, marker in QUESTION_MARKERS.items():
                if marker in transcript:
                    for q in QUESTIONS:
                        if q["id"] == q_id:
                            current_question = q
                            logger.info(f"Agent asking question {q_id}")
                            break
                    break

    # @session.on("agent_speech_committed")
    # def on_agent_speech(transcript: str):
    #     logger.info(f"Agent: {transcript}")
        
    #     nonlocal current_question
        
    #     detected_question = detect_question_id(transcript)
        
    #     if detected_question:
    #         current_question = detected_question
    #         logger.info(f"Agent asking question {detected_question['id']}: {detected_question['text'][:50]}...")
    #     else:
    #         logger.debug(f"Could not detect question from agent speech: {transcript[:100]}")
       

    # Start the agent session
    await session.start(agent=InsightAIAgent(), room=ctx.room)

    # Generate the initial greeting and first question
    # This is what triggers the agent to start speaking
    await session.generate_reply(
        instructions="السلام علیکم۔ صارف کو خوش آمدید کہیں۔ پھر پہلا سوال پوچھیں۔"
    )

if __name__ == "__main__":
    cli.run_app(server)
    
    
# """آپ ایک ماہر مارکیٹ ریسرچ اسسٹنٹ ہیں۔ آپ کا نام 'InsightAI' ہے۔

# آپ کا مقصد یہ انٹرویو مکمل کرنا ہے۔ براہ کرم درج ذیل سوالات ترتیب سے پوچھیں:

# سوالات:
# {json.dumps(QUESTIONS, ensure_ascii=False)}

# سخت قوانین (Logic Rules):
# 1. ہمیشہ اردو میں بات کریں۔
# 2. ایک وقت میں صرف ایک سوال پوچھیں۔
# 3. سوالات کے جوابات سن کر پھر سوال پوچھیں، لیکن کبھی بھی جواب کو دہرانا نہیں ہے۔ صارف کے جوابات سنیں اور سمجھیں۔
# 4. جب سوالات پوچھیں، تو ہر لفظ کی درست اور صاف تلفظ کی کوشش کریں۔
# 5. سوال 5 کے بعد برانچنگ لاجک:
#    - اگر صارف کا جواب 1 سے 4 کے درمیان ہو، تو سوال 6 (وجہ پوچھنا) لازمی پوچھیں۔
#    - اگر جواب 5 یا اس سے اوپر ہو، تو سوال 6 کو چھوڑ دیں اور سوال 7 پوچھیں۔
# 6. جب تمام سوالات مکمل ہو جائیں، تو 'شکریہ' کہہ کر انٹرویو ختم کریں۔

# ہمیشہ صارف کے جوابات کا انتظار کریں اور پھر لاجک کے مطابق اگلا سوال پوچھیں۔"""