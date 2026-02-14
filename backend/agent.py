import logging
import json
from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, llm
from livekit.plugins import groq, deepgram, silero, azure

load_dotenv(".env.local")
logger = logging.getLogger("insight-ai")
server = AgentServer()
 
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

class InsightAIAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=f"""آپ ایک ماہر مارکیٹ ریسرچ اسسٹنٹ ہیں۔ آپ کا نام 'InsightAI' ہے۔

آپ کا مقصد یہ انٹرویو مکمل کرنا ہے۔ براہ کرم درج ذیل سوالات ترتیب سے پوچھیں:

سوالات:
{json.dumps(QUESTIONS, ensure_ascii=False)}

سخت قوانین (Logic Rules):
1. ہمیشہ اردو میں بات کریں۔
2. ایک وقت میں صرف ایک سوال پوچھیں۔
3. سوالات کے جوابات سن کر پھر سوال پوچھیں، لیکن کبھی بھی جواب کو دہرانا نہیں ہے۔ صارف کے جوابات سنیں اور سمجھیں۔
4. جب سوالات پوچھیں، تو ہر لفظ کی درست اور صاف تلفظ کی کوشش کریں۔
5. سوال 5 کے بعد برانچنگ لاجک:
   - اگر صارف کا جواب 1 سے 4 کے درمیان ہو، تو سوال 6 (وجہ پوچھنا) لازمی پوچھیں۔
   - اگر جواب 5 یا اس سے اوپر ہو، تو سوال 6 کو چھوڑ دیں اور سوال 7 پوچھیں۔
6. جب تمام سوالات مکمل ہو جائیں، تو 'شکریہ' کہہ کر انٹرویو ختم کریں۔

ہمیشہ صارف کے جوابات کا انتظار کریں اور پھر لاجک کے مطابق اگلا سوال پوچھیں۔"""
        )

@server.rtc_session()
async def my_agent(ctx: JobContext):
    logger.info(f"Starting InsightAI session for room: {ctx.room.name}")

    session = AgentSession(
        stt=deepgram.STT(language="ur"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=azure.TTS(voice="ur-PK-UzmaNeural"),
        vad=silero.VAD.load()
    )

    # Observability: Print the conversation flow in the console
    @session.on("user_speech_committed")
    def on_user_speech(transcript: str):
        logger.info(f"User: {transcript}")

    @session.on("agent_speech_committed")
    def on_agent_speech(transcript: str):
        logger.info(f"Agent: {transcript}")

    # Start the agent session
    await session.start(agent=InsightAIAgent(), room=ctx.room)

    # Generate the initial greeting and first question
    # This is what triggers the agent to start speaking
    await session.generate_reply(
        instructions="السلام علیکم۔ صارف کو خوش آمدید کہیں۔ پھر پہلا سوال پوچھیں۔"
    )

if __name__ == "__main__":
    cli.run_app(server)








# import logging
# import json
# from dotenv import load_dotenv
# from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, llm
# from livekit.plugins import groq, deepgram, silero, azure

# load_dotenv(".env.local")
# logger = logging.getLogger("insight-ai")
# server = AgentServer()

# # 1. Your Structured Questionnaire
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
#             instructions=f"""آپ ایک ماہر مارکیٹ ریسرچ اسسٹنٹ ہیں۔ آپ کا نام 'InsightAI' ہے۔

# آپ کا مقصد یہ انٹرویو مکمل کرنا ہے۔ براہ کرم درج ذیل سوالات ترتیب سے پوچھیں:

# سوالات:
# {json.dumps(QUESTIONS, ensure_ascii=False)}

# سخت قوانین (Logic Rules):
# 1. ہمیشہ اردو میں بات کریں۔
# 2. ایک وقت میں صرف ایک سوال پوچھیں۔
# 3. صارف کے جوابات سنیں اور سمجھیں۔
# 4. سوال 5 کے بعد برانچنگ لاجک:
#    - اگر صارف کا جواب 1 سے 4 کے درمیان ہو، تو سوال 6 (وجہ پوچھنا) لازمی پوچھیں۔
#    - اگر جواب 5 یا اس سے اوپر ہو، تو سوال 6 کو چھوڑ دیں اور سوال 7 پوچھیں۔
# 5. جب تمام سوالات مکمل ہو جائیں، تو 'شکریہ' کہہ کر انٹرویو ختم کریں۔

# ہمیشہ صارف کے جوابات کا انتظار کریں اور پھر لاجک کے مطابق اگلا سوال پوچھیں۔"""
#         )

# @server.rtc_session()
# async def my_agent(ctx: JobContext):
#     logger.info(f"Starting InsightAI session for room: {ctx.room.name}")

#     session = AgentSession(
#         stt=deepgram.STT(language="ur"),
#         llm=groq.LLM(model="llama-3.3-70b-versatile"),
#         tts=azure.TTS(voice="ur-PK-UzmaNeural"),
#         vad=silero.VAD.load()
#     )

#     # Observability: Print the conversation flow in the console
#     @session.on("user_speech_committed")
#     def on_user_speech(transcript: str):
#         logger.info(f"User: {transcript}")

#     @session.on("agent_speech_committed")
#     def on_agent_speech(transcript: str):
#         logger.info(f"Agent: {transcript}")

#     # Start the agent session
#     await session.start(agent=InsightAIAgent(), room=ctx.room)

#     # Generate the initial greeting and first question
#     # This is what triggers the agent to start speaking
#     await session.generate_reply(
#         instructions="السلام علیکم۔ صارف کو خوش آمدید کہیں۔ پھر پہلا سوال پوچھیں۔"
#     )

# if __name__ == "__main__":
#     cli.run_app(server)
    
   
   
   
   
   
   
   
   
   
    
    
# import logging
# import json
# from dotenv import load_dotenv
# from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, llm
# from livekit.plugins import groq, deepgram, silero, azure

# load_dotenv(".env.local")
# logger = logging.getLogger("insight-ai")
# server = AgentServer()

# # 1. Your Structured Questionnaire
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
#     def __init__(self, chat_ctx: llm.ChatContext):
#         super().__init__(
#             instructions=f"""آپ ایک ماہر مارکیٹ ریسرچ اسسٹنٹ ہیں۔ آپ کا نام 'InsightAI' ہے۔
#             آپ کا مقصد یہ انٹرویو مکمل کرنا ہے: {json.dumps(QUESTIONS, ensure_ascii=False)}

#             سخت قوانین (Logic Rules):
#             1. ہمیشہ اردو میں بات کریں۔
#             2. ایک وقت میں صرف ایک سوال پوچھیں۔
#             3. سوال 5 کے بعد برانچنگ لاجک:
#                - اگر صارف کا جواب 1 سے 4 کے درمیان ہو، تو سوال 6 (وجہ پوچھنا) لازمی پوچھیں۔
#                - اگر جواب 5 یا اس سے اوپر ہو، تو سوال 6 کو بالکل نہ پوچھیں اور سیدھا سوال 7 پر جائیں۔
#             4. جب تمام سوالات مکمل ہو جائیں، تو 'شکریہ' کہہ کر انٹرویو ختم کریں۔
#             """,
#             chat_ctx=chat_ctx
#         )

# @server.rtc_session()
# async def my_agent(ctx: JobContext):
#     # Initialize ChatContext to track the state of the conversation
#     logger.info(f"Starting InsightAI session for room: {ctx.room.name}")

#     # 1. Initialize an empty ChatContext
#     chat_ctx = llm.ChatContext()
    
#     # 2. Correctly add the system message using add_message()
#     chat_ctx.add_message(
#         role="system",
#         content="آپ انٹرویو لے رہے ہیں۔ صارف کے جوابات کو ٹریک کریں اور لاجک کے مطابق اگلا سوال پوچھیں۔"
#     )

#     session = AgentSession(
#         stt=deepgram.STT(language="ur"),
#         llm=groq.LLM(model="llama-3.3-70b-versatile"),
#         tts=azure.TTS(voice="ur-PK-UzmaNeural"),
#         vad=silero.VAD.load()
#     )

#     # Observability: Print the conversation flow in the console
#     @session.on("user_speech_committed")
#     def on_user_speech(transcript: str):
#         print(f"Respondent: {transcript}")

#     @session.on("agent_speech_committed")
#     def on_agent_speech(transcript: str):
#         print(f"InsightAI: {transcript}")

#     await session.start(agent=InsightAIAgent(chat_ctx), room=ctx.room)

#     # Trigger the first question
#     await session.generate_reply(
#         instructions=f"انٹرویو کا آغاز کریں اور پہلا سوال پوچھیں: {QUESTIONS[0]['text']}"
#     )

# if __name__ == "__main__":
#     cli.run_app(server)