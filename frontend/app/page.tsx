'use client';

import { useState, useEffect } from 'react';
import { AgentSession } from '@/components/agent-session';
import { Mic } from 'lucide-react';

const translations = {
  en: {
    startButton: 'Start Interview',
    connecting: 'Connecting...',
    heading: 'RIO: Automated CLT',
    powered: 'powered by',
    insightai: 'InsightAI.'
  },
  ur: {
    startButton: 'انٹرویو شروع کریں',
    connecting: 'منسلک ہو رہے ہیں...',
    heading: 'RIO: Automated CLT',
    powered: 'سے طاقت حاصل',
    insightai: 'InsightAI.'
  },
  roman: {
    startButton: 'Interview Shuru Karein',
    connecting: 'Connect ho rahe hain...',
    heading: 'RIO: Automated CLT',
    powered: 'powered by',
    insightai: 'InsightAI.'
  }
};

export default function InterviewPage() {
  const [isConnected, setIsConnected] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [language, setLanguage] = useState<'en' | 'ur' | 'roman'>('ur');

  // Detect language changes from document class
  useEffect(() => {
    const detectLanguage = () => {
      const root = document.documentElement;
      if (root.classList.contains('urdu')) {
        setLanguage('ur');
      } else if (root.classList.contains('roman')) {
        setLanguage('roman');
      } else {
        setLanguage('en');
      }
    };

    detectLanguage();

    // Watch for language changes
    const observer = new MutationObserver(detectLanguage);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

    return () => observer.disconnect();
  }, []);

  // Set light mode as default on mount
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('dark-mode');
    root.classList.add('light-mode');
  }, []);

  const t = translations[language];

  return (
    <div className="landing-container interview-page">
      {/* Company Name */}
      <div className="company-name">
        {t.powered} <span className="company-name-bold">{t.insightai}</span>
      </div>

      <div className="content-center">
        {/* Heading */}
        <h1 className="interview-heading">
          {t.heading}
        </h1>

        {/* Start Interview Button */}
        {!isConnected ? (
          <button
            className="start-button"
            onClick={() => setIsConnected(true)}
          >
            {t.startButton}
          </button>
        ) : (
          <>
            {/* Mic Button - Static, no wave for now */}
            <button
              className="mic-button"
              disabled={true}
            >
              <Mic size={48} />
            </button>

            {/* Hidden AgentSession - just connects and plays audio */}
            <AgentSession
              onConnect={() => {
                console.log('Connected to agent');
              }}
              onDisconnect={() => {
                setIsConnected(false);
              }}
            />
          </>
        )}
      </div>
    </div>
  );
}