# import logging
# import json
# import os
# from dotenv import load_dotenv
# from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli
# from livekit.plugins import google, silero
# from livekit.plugins.google.beta import realtime

# load_dotenv(".env.local")
# logger = logging.getLogger("insight-ai")
# server = AgentServer()

# QUESTIONS = [
#     {"id": "1", "text": "آپ کا جینڈر کیا ہے؟ مرد یا عورت", "type": "general"},
#     {"id": "2", "text": "اپنی عمر بتائیں۔", "type": "general"},
#     {"id": "3", "text": "آپ کو ریو بسکٹ دیکھنے میں کیسا لگا؟ 1 سے 7 کے اسکیل پر بتائیں، جہاں 1 کا مطلب ہے 'بالکل بھی پسند نہیں آیا' اور 7 کا مطلب ہے 'بہت پسند آیا'۔", "type": "general"},
#     {"id": "4", "text": "برائے مہربانی بتائیں کہ آپ کو ریو کا ذائقہ کس حد تک پسند آیا؟ 1 سے 7 کے اسکیل پر جہاں 1 کا مطلب ہے بالکل بھی پسند نہیں آیا اور 7 کا مطلب ہے بہت پسند آیا۔", "type": "general"},
#     {"id": "5", "text": "مجموعی طور پر آپ کو ریو کیسا لگا؟ 1 سے 9 کے اسکیل پر بتائیں، جہاں 1 کا مطلب ہے 'بالکل بھی پسند نہیں آیا' اور 9 کا مطلب ہے 'بہت پسند آیا'۔", "type": "general"},
#     {"id": "6", "text": "آپ کے جواب سے لگتا ہے آپ کو ریو نہیں پسند آیا۔ برائے مہربانی تفصیل سے بتائیں کیوں پسند نہیں آیا؟", "type": "conditional"},
#     {"id": "7", "text": "اگر ریو بسکٹ کے 2 بسکٹ کا پیک 30 روپے میں دستیاب ہو، تو کیا آپ اسے خریدیں گے؟ 1، جی ہاں خریدوں گا، 2، نہیں خریدوں گا، 3، شاید یا کچھ کہہ نہیں سکتا۔", "type": "general"},
#     {"id": "8", "text": "کیا آپ ریو کے بارے میں کچھ اور کہنا چاہیں گے یا کوئی مشورہ دینا چاہیں گے؟", "type": "general"}
# ]

# class InsightAIAgent(Agent):
#     def __init__(self):
#         super().__init__(
#             instructions=f"""
# You are an expert market research assistant conducting an interview about Rio biscuit. Your name is InsightAI.

# **Questions to ask in order:**
# {json.dumps(QUESTIONS, ensure_ascii=False)}

# **Strict Rules:**
# 1. Always speak in Urdu only.
# 2. Ask only one question at a time.
# 3. Listen carefully to responses, then ask the next question.
# 4. Branching logic after Question 5:
#    - If the user's answer is between 1 and 4, ask Question 6.
#    - If the answer is 5 or above, skip Question 6 and go to Question 7.
# 5. When all questions are done, thank the respondent and end the interview.
# 6. Never repeat the user's response back to them.
# 7. Do not repeat a question unless the respondent asks for clarity.
# 8. Do not thank the respondent after each answer. Only thank them at the very end.
# 9. Be conversational, clear, and concise.
#             """
#         )

# @server.rtc_session()
# async def my_agent(ctx: JobContext):
#     session_id = ctx.job.id
#     logger.info(f"Starting InsightAI session {session_id} for room: {ctx.room.name}")

#     session = AgentSession(
#         llm=realtime.RealtimeModel(
#             # model="gemini-2.5-flash",
#             modalities=["AUDIO"],   # full audio in, audio out — no STT/TTS needed
#             # language="ur",
#             temperature=0.7,
#         )
#     )

#     @session.on("user_input_transcribed")
#     def on_user_input(event):
#         if not event.is_final:
#             return
#         logger.info(f"User: {event.transcript}")

#     @session.on("conversation_item_added")
#     def on_conversation_item(event):
#         if event.item.role == "assistant":
#             logger.info(f"Agent: {event.item.text_content}")

#     await session.start(agent=InsightAIAgent(), room=ctx.room)

#     await session.generate_reply(
#         instructions="السلام علیکم۔ صارف کو خوش آمدید کہیں۔ پھر پہلا سوال پوچھیں۔"
#     )

# if __name__ == "__main__":
#     cli.run_app(server)

import logging
import json
import os
import asyncio
from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli
from livekit.plugins.google.beta import realtime
from supabase import create_client, Client

load_dotenv(".env.local")
logger = logging.getLogger("insight-ai")
server = AgentServer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# markers to detect which question the agent just asked
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

async def save_response_to_supabase(session_id: str, question_id: str, question_text: str, response: str):
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
You are an expert market research assistant conducting an interview about Rio biscuit. Your name is InsightAI.

**Questions to ask in order:**
{json.dumps(QUESTIONS, ensure_ascii=False)}

**Strict Rules:**
1. Always speak in Urdu only.
2. Ask only one question at a time.
3. Listen carefully to responses, then ask the next question.
4. Branching logic after Question 5:
   - If the user's answer is between 1 and 4, ask Question 6.
   - If the answer is 5 or above, skip Question 6 and go to Question 7.
5. When all questions are done, thank the respondent and end the interview.
6. Never repeat the user's response back to them - Never say "You said [response]" or anything like that. Just listen and move on to the next question.
7. Do not repeat a question unless the respondent asks for clarity.
8. Do not thank the respondent after each answer. Only thank them at the very end.
9. Be conversational, clear, and concise.
            """
        )

@server.rtc_session()
async def my_agent(ctx: JobContext):
    session_id = ctx.job.id
    logger.info(f"Starting InsightAI session {session_id} for room: {ctx.room.name}")

    session = AgentSession(
        llm=realtime.RealtimeModel(
            modalities=["AUDIO"],
            temperature=0.7,
        )
    )

    current_question = None
    last_saved_response = None

    @session.on("conversation_item_added")
    def on_conversation_item(event):
        nonlocal current_question

        if event.item.role == "assistant":
            transcript = event.item.text_content
            if not transcript:
                return

            logger.info(f"Agent: {transcript}")

            # detect which question the agent just asked
            transcript_lower = transcript.lower()
            for q_id, marker in QUESTION_MARKERS.items():
                if marker in transcript_lower:
                    for q in QUESTIONS:
                        if q["id"] == q_id:
                            current_question = q
                            logger.info(f"Agent asking question {q_id}")
                            break
                    break

    @session.on("user_input_transcribed")
    def on_user_input(event):
        nonlocal last_saved_response

        if not event.is_final:
            return

        transcript = event.transcript
        logger.info(f"User: {transcript}")

        # only save if we know which question was asked and it's a new response
        if current_question and last_saved_response != transcript:
            last_saved_response = transcript
            asyncio.create_task(
                save_response_to_supabase(
                    session_id,
                    current_question["id"],
                    current_question["text"],
                    transcript
                )
            )
        elif not current_question:
            logger.warning("User responded but no current question tracked — response not saved")

    await session.start(agent=InsightAIAgent(), room=ctx.room)

    await session.generate_reply(
        instructions="السلام علیکم۔ صارف کو خوش آمدید کہیں۔ پھر پہلا سوال پوچھیں۔"
    )

if __name__ == "__main__":
    cli.run_app(server)