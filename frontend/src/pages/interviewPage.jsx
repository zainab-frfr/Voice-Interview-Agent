import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import HamburgerMenu from '../components/hamburgerMenu';
import { Mic, Square } from "lucide-react";
import { api } from '../services/api';

import packaging from '../images/packaging.jpg';
import packaging1 from '../images/packaging1.jpg';
import packaging2 from '../images/packaging2.jpg';



/* ---------------- Unlock audio after user interaction ---------------- */
function waitForUserGesture() {
  return new Promise((resolve) => {
    const unlock = () => {
      localStorage.setItem("user_interacted", "true");
      window.removeEventListener("click", unlock);
      window.removeEventListener("touchstart", unlock);
      resolve();
    };

    if (localStorage.getItem("user_interacted") === "true") {
      return resolve();
    }

    window.addEventListener("click", unlock);
    window.addEventListener("touchstart", unlock);
  });
}

export default function InterviewPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  const [sessionId, setSessionId] = useState('');
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const [transcription, setTranscription] = useState('');
  const [animatedText, setAnimatedText] = useState('');
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);

  const currentQuestion = questions[currentQuestionIndex];

  /* ---------------- Initialize Interview ---------------- */
  useEffect(() => {
    initializeInterview();
  }, []);

  const initializeInterview = async () => {
    try {
      const newSessionId = api.generateSessionId();
      setSessionId(newSessionId);

      const data = await api.getQuestions();
      setQuestions(data.questions);

      await api.startInterview(newSessionId);

      if (data.questions.length > 0) {
        await playQuestion(data.questions[0].text);
      }
    } catch (err) {
      setError('Failed to initialize interview');
      console.error(err);
    }
  };

  /* ---------------- Play Question Audio ---------------- */
  const playQuestion = async (text) => {
    try {
      setIsPlayingAudio(true);
      setError('');

      await waitForUserGesture();

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }

      const audioBlob = await api.textToSpeech(text);
      const audioUrl = URL.createObjectURL(audioBlob);

      audioRef.current.src = audioUrl;
      audioRef.current.load();
      await audioRef.current.play();

      audioRef.current.onended = () => {
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
      };
    } catch (err) {
      setIsPlayingAudio(false);
     // setError("Tap anywhere to enable audio");
    }
  };

  /* ---------------- Animated Typing Effect ---------------- */
  useEffect(() => {
    if (!currentQuestion) return;

    const fullText = t(currentQuestion.id);
    setAnimatedText('');

    if (!isPlayingAudio) {
      setAnimatedText(fullText);
      return;
    }

    let index = 0;
    const interval = setInterval(() => {
      index++;
      setAnimatedText(fullText.slice(0, index));
      if (index >= fullText.length) clearInterval(interval);
    }, 30);

    return () => clearInterval(interval);
  }, [currentQuestionIndex, isPlayingAudio, i18n.language]);

  /* ---------------- Recording Logic ---------------- */
  const startRecording = async () => {
    try {
      setError('');
      setTranscription('');

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        await processRecording(audioBlob);
      };

      recorder.start();
      setIsRecording(true);
    } catch {
      setError("Microphone permission denied");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processRecording = async (audioBlob) => {
    setIsProcessing(true);
    try {
      const q = questions[currentQuestionIndex];

      const result = await api.speechToText(
        audioBlob,
        sessionId,
        q.id,
        q.text,
        q.type,
        currentQuestionIndex
      );

      setTranscription(result.text);
      setTimeout(goToNextQuestion, 2000);
    } catch {
      setError("Transcription failed");
    } finally {
      setIsProcessing(false);
    }
  };

  const goToNextQuestion = async () => {
    if (currentQuestionIndex < questions.length - 1) {
      const nextIndex = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIndex);
      setTranscription('');
      await playQuestion(questions[nextIndex].text);
    } else {
      await api.completeInterview(sessionId);
      navigate('/end');
    }
  };

  const progress = questions.length
    ? ((currentQuestionIndex + 1) / questions.length) * 100
    : 0;

  // Check if current question requires images
  const showSingleImage = currentQuestion && ['Q15', 'Q15a', 'Q15b'].includes(currentQuestion.id);
  const showDoubleImage = currentQuestion && currentQuestion.id === 'Q17';

  /* ---------------- UI ---------------- */
  return (
    <div className="landing-container interview-page">
      <audio ref={audioRef} />
      <HamburgerMenu />

      <div className="content-center">

        {/* Heading */}
        <h1 className="interview-heading">
          {t("interview_page_heading")}
        </h1>

        {/* Progress */}
        <div className="progress-container">
          <div className="progress-text">
            Question {currentQuestionIndex + 1} of {questions.length}
          </div>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Single Image Display for Q15, Q15a, Q15b */}
        {showSingleImage && (
          <div className="image-container single-image">
           <img src={packaging} alt="Biscuit Packaging" className="product-image" />

          </div>
        )}

        {/* Double Image Display for Q17 */}
        {showDoubleImage && (
          <div className="image-container double-image">
            <div className="image-wrapper">
              <img src={packaging1} alt="Packaging 1" className="product-image" />
              <span className="image-label">Package 1</span>
            </div>
            <div className="image-wrapper">
             <img src={packaging2} alt="Packaging 2" className="product-image" />
              <span className="image-label">Package 2</span>
            </div>
          </div>
        )}

        {/* SINGLE FIXED MIC BUTTON */}
        <button
          className={`mic-button
            ${isRecording ? 'recording' : ''}
            ${isPlayingAudio ? 'playing' : ''}
            ${isProcessing ? 'processing' : ''}
          `}
          onClick={() => {
            if (isPlayingAudio || isProcessing) return;
            if (isRecording) stopRecording();
            else startRecording();
          }}
          disabled={isPlayingAudio || isProcessing}
        >

          {isPlayingAudio && (
            <div className="wave-icon">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}

          {isRecording && !isPlayingAudio && (
            <Square size={48} />
          )}

          {!isRecording && !isPlayingAudio && !isProcessing && (
            <Mic size={48} />
          )}

          {isProcessing && <div className="spinner"></div>}
        </button>

        {/* Animated Question Text */}
        {currentQuestion && (
          <div className="question-caption">
            <h2 className={isPlayingAudio ? "typing" : ""}>
              {animatedText}
            </h2>
          </div>
        )}

        {/* Transcription */}
        {transcription && (
          <div className="transcription-box">
            <h3>Your Answer</h3>
            <p>{transcription}</p>
          </div>
        )}

        {error && <div className="error-text">{error}</div>}
      </div>
    </div>
  );
}