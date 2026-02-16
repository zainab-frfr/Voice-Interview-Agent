# InsightAI - Voice-Based Interview Agent

A LiveKit-powered voice agent that conducts structured market research interviews in Urdu. The agent asks questions, captures responses, and stores them in Supabase.

## Features

- 🎙️ Real-time voice conversation in Urdu
- 📝 8-question structured interview format
- 💾 Responses stored in Supabase database
- 🌐 Cloud-deployed agent with LiveKit
- 📊 Export data as CSV with proper UTF-8 encoding

## Architecture

**Frontend:** Next.js (React) with minimal UI  
**Backend:** Python LiveKit Agent  
**Speech-to-Text:** Deepgram (Urdu)  
**Text-to-Speech:** Azure Cognitive Services (Urdu)  
**LLM:** Groq (llama-3.3-70b-versatile)  
**Database:** Supabase PostgreSQL  
**Voice Infrastructure:** LiveKit Cloud

## Prerequisites

- Python 3.12+
- Node.js 18+
- Git
- Accounts for:
  - [LiveKit Cloud](https://cloud.livekit.io)
  - [Supabase](https://supabase.com)
  - [Groq API](https://console.groq.com)
  - [Deepgram](https://console.deepgram.com)
  - [Azure](https://azure.microsoft.com) (for TTS)

## Project Setup

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd insightai-agent
```

### 2. Backend Setup (Agent)

#### Create Python Virtual Environment

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
uv pip install -r requirements.txt
```

Or if using uv with pyproject.toml:

```bash
uv sync
```

#### Create `.env.local` File

```bash
cp .env.example .env.local
```

Edit `.env.local` with your credentials:

```env
# LiveKit
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Groq
GROQ_API_KEY=your_groq_api_key

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_api_key

# Azure TTS
AZURE_TTS_REGION=eastus
AZURE_TTS_KEY=your_azure_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

#### Run Agent in Development

```bash
uv run agent.py dev
```

The agent will:
- Start a local HTTP server (usually on port 57xxx)
- Register with LiveKit Cloud
- Wait for interview requests

### 3. Frontend Setup (Web Interface)

#### Install Dependencies

```bash
cd ../frontend
npm install
```

#### Create `.env.local` File

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
NEXT_PUBLIC_LIVEKIT_TOKEN=<will-be-generated-by-backend>
```

#### Run Frontend

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Supabase Setup

#### Create Database Table

In Supabase SQL Editor, run:

```sql
CREATE TABLE live_responses (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  session_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  question TEXT NOT NULL,
  response TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interview_responses_session_id ON live_responses(session_id);
```

## Running an Interview

1. **Start the agent:**
   ```bash
   cd backend
   uv run agent.py dev
   ```
   Wait for: `registered worker` message

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open browser:**
   Go to http://localhost:3000

4. **Click "Start Interview"**
   - Microphone will activate
   - Agent greets you in Urdu
   - Speak your answers clearly

5. **Interview completes:**
   - Responses are saved to Supabase
   - Session ends after final question

## Exporting Data

### As CSV (Recommended)

1. Go to Supabase Dashboard
2. Select `live_responses` table
3. Click download icon → "Download as CSV"

### Using Python Script (Colab)

```python
import json
import pandas as pd

# Upload your JSON export from Supabase

with open('live_responses_rows.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def fix_urdu_text(text):
    if isinstance(text, str):
        try:
            return text.encode('latin-1').decode('utf-8')
        except:
            return text
    return text

for row in data:
    row['question'] = fix_urdu_text(row['question'])
    row['response'] = fix_urdu_text(row['response'])

df = pd.DataFrame(data)
df.to_csv('responses.csv', index=False, encoding='utf-8')
print("✅ CSV exported successfully!")
```

## Troubleshooting

### Agent won't register with LiveKit

**Error:** `Connection refused` or timeout

**Solution:**
- Check LiveKit credentials in `.env.local`
- Verify LiveKit Cloud project is active
- Check internet connection

### User can't hear agent or agent can't hear user

**Error:** Audio not working

**Solution:**
- Check microphone/speaker permissions in browser
- Reload page and try again
- Check browser console for errors
- Verify Azure TTS is configured correctly

### Urdu text appears as gibberish (ØÙ„Ø¨)

**Solution:**
- Export as JSON from Supabase
- Use the Python decoding script above
- Open CSV in Excel with UTF-8 encoding

### "inference is slower than realtime" warning

**Meaning:** System is running slow

**Solution:**
- Close other programs
- Deploy agent to cloud server (Railway, Render)
- Use faster laptop/computer

### Questions are being skipped

**Solution:**
This is a known issue with question detection. The agent uses keyword matching:
- Ensure agent instructions include all questions
- Check logs for "Agent asking question X" messages
- Review saved responses in Supabase

## Project Structure

```
insightai-agent/
├── backend/
│   ├── agent.py              # Main agent code
│   ├── requirements.txt       # Python dependencies
│   └── .env.local            # API keys (create this)
│
├── frontend/
│   ├── pages/
│   │   └── index.tsx         # Main interview page
│   ├── components/           # React components
│   ├── next.config.js
│   └── package.json
│
└── README.md
```

## Questions in Interview

1. **Gender** - Male or Female?
2. **Age** - How old are you?
3. **Visual Appeal** - Rate appearance (1-7 scale)
4. **Taste** - Rate taste (1-7 scale)
5. **Overall** - Overall rating (1-9 scale)
6. **Why Not** - (Conditional) Why didn't you like it? (if Q5 score is 1-4)
7. **Purchase Intent** - Would you buy at 30 PKR? (Yes/No/Maybe)
8. **Suggestions** - Any other comments or suggestions?

## Performance Tips

- **Local Development:** Agent runs on your computer. Expect 0.3-0.5s latency
- **Cloud Deployment:** Deploy to Railway/Render for <100ms latency
- **Best Experience:** Run both frontend and backend on cloud servers

## Deployment

### Deploy Agent to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

## API Keys Setup Guide

### LiveKit Cloud
1. Go to https://cloud.livekit.io
2. Create a project
3. Copy: URL, API Key, API Secret

### Groq
1. Go to https://console.groq.com/keys
2. Create API key
3. Copy key

### Deepgram
1. Go to https://console.deepgram.com/
2. Create API key
3. Copy key

### Azure TTS
1. Go to https://portal.azure.com
2. Create "Speech Services" resource
3. Copy: Key and Region

### Supabase
1. Go to https://supabase.com
2. Create project
3. Go to Settings → API → Copy anon key

## Support

For issues:
1. Check logs in terminal
2. Check browser console (F12)
3. Review Supabase logs
4. Check API credential validity

## License

MIT

## Author

InsightAI Team