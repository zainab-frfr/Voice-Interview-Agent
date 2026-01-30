// api.jsx

// Base API URL (from .env or fallback)
const API_URL = import.meta.env.VITE_API_URL || "https://wrong-layney-a2z2-5a17c1e7.koyeb.app";

// Enable ngrok header only when explicitly set in .env
// Add this in your .env:  VITE_USE_NGROK_SKIP=true
const USE_NGROK_SKIP = import.meta.env.VITE_USE_NGROK_SKIP === "true";

//
// --- Universal fetch wrapper ---
// Automatically:
// - adds Accept: application/json
// - adds ngrok-skip-browser-warning header when using ngrok
// - preserves user-specified headers
//
async function safeFetch(path, options = {}) {
  const url = `${API_URL}${path.startsWith("/") ? path : "/" + path}`;

  const defaultHeaders = {
    Accept: "application/json",
  };

  // merge headers
  options.headers = {
    ...defaultHeaders,
    ...(options.headers || {}),
  };

  // apply ngrok skip header only if enabled
  if (USE_NGROK_SKIP) {
    options.headers["ngrok-skip-browser-warning"] = "69420";
  }

  return fetch(url, options);
}

//
// --- API functions ---
//
export const api = {
  // Generate unique session ID
  generateSessionId: () =>
    `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,

  // Get all questions
  getQuestions: async () => {
    const response = await safeFetch("/get-questions", { method: "GET" });
    if (!response.ok) throw new Error("Failed to fetch questions");
    return response.json();
  },

  // Start interview session
  startInterview: async (sessionId) => {
    const response = await safeFetch("/start-interview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) throw new Error("Failed to start interview");
    return response.json();
  },

  // Text-to-Speech
  textToSpeech: async (text) => {
    const response = await safeFetch(`/tts?text=${encodeURIComponent(text)}`, {
      method: "POST",
    });

    if (!response.ok) throw new Error("TTS failed");
    return response.blob();
  },

  // Speech-to-Text (multipart/form-data)
  speechToText: async (audioBlob, sessionId, questionId, questionText, questionType, responseOrder) => {
    try {
      // Create FormData
      const formData = new FormData();
      
      // Convert blob to file with proper naming
      const audioFile = new File([audioBlob], 'recording.webm', {
        type: 'audio/webm'
      });
      
      formData.append('file', audioFile);
      
      // Build query string with all required parameters
      const params = new URLSearchParams({
        session_id: sessionId || '',
        question_id: questionId || '',
        question_text: questionText || '',
        question_type: questionType || '',
        response_order: responseOrder.toString() || '0'
      });

      console.log('Sending STT request:', {
        sessionId,
        questionId,
        questionType,
        responseOrder,
        blobSize: audioBlob.size
      });

      // ⚠️ IMPORTANT: Use API_URL (not API_BASE_URL) and don't use safeFetch
      // because we need to send FormData without JSON headers
      const url = `${API_URL}/stt?${params.toString()}`;
      
      const headers = {};
      if (USE_NGROK_SKIP) {
        headers["ngrok-skip-browser-warning"] = "69420";
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: formData
        // Don't set Content-Type header - browser will set it with boundary
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('STT API Error Response:', errorText);
        throw new Error(`STT failed: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('STT Success:', result);
      return result;

    } catch (error) {
      console.error('STT Request Error:', error);
      throw error;
    }
  },

  // Complete interview
  completeInterview: async (sessionId) => {
    const response = await safeFetch(`/complete-interview/${sessionId}`, {
      method: "POST",
    });

    if (!response.ok) throw new Error("Failed to complete interview");
    return response.json();
  },

  // Get interview data
  getInterview: async (sessionId) => {
    const response = await safeFetch(`/get-interview/${sessionId}`, {
      method: "GET",
    });

    if (!response.ok) throw new Error("Failed to get interview");
    return response.json();
  },

  // Generate CSV
  generateCSV: async (sessionId) => {
    const response = await safeFetch(`/generate-csv/${sessionId}`, {
      method: "POST",
    });

    if (!response.ok) throw new Error("Failed to generate CSV");
    return response.blob();
  },
};