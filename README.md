# Voice Interview Agent 🎤

A full-stack prototype of a real-time voice interaction agent. This project is structured into a modular backend and frontend to handle audio processing and user interaction separately.

---

## 📂 Project Structure

- **`/backend`**: Core logic, including speech-to-text (STT), database storage, and text-to-speech (TTS).
- **`/frontend`**: The user interface for recording audio and displaying real-time transcripts.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+ 
* Node.js 18+
* API Keys for: Deepgram, ElevenLabs, Supabase (URL + API Key)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/zainab-frfr/Voice-Interview-Agent.git
   cd prototype

2. **Set up Backend**
   ```bash
   cd backend 
   pip install -r requirements.txt 

   # Create .env and add keys
   echo "DEEPGRAM_API_KEY=\nELEVENLABS_API_KEY=\nSUPABASE_URL=\nSUPABASE_KEY=" > .env

   uvicorn main:app --reload


3. **Set up Frontend**

   ```bash
   cd frontend 
   npm install 

   # Create .env and add keys
   echo "VITE_API_URL=\nVITE_USE_NGROK_SKIP=" > .env
   # VITE_API_URL is the backend home route 
   # VITE_USE_NGROK_SKIP is a boolean flag that should be set to true. 

   npm run dev