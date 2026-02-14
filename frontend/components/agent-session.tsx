'use client';

import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';
import { useEffect, useState } from 'react';

interface AgentSessionProps {
  onConnect: () => void;
  onDisconnect: () => void;
}

export function AgentSession({ onConnect, onDisconnect }: AgentSessionProps) {
  const [token, setToken] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [serverUrl, setServerUrl] = useState<string>('');

  const roomName = 'interview-room';
  const participantName = `user-${Math.random().toString(36).substr(2, 9)}`;

  useEffect(() => {
    const getToken = async () => {
      try {
        setIsLoading(true);
        
        // Get server URL from env
        const url = process.env.NEXT_PUBLIC_LIVEKIT_URL;
        if (!url) {
          throw new Error('NEXT_PUBLIC_LIVEKIT_URL not configured');
        }
        setServerUrl(url);

        // Get token from backend
        const response = await fetch(
          `/api/token?room=${roomName}&participant=${participantName}`
        );

        if (!response.ok) {
          throw new Error('Failed to get token');
        }

        const data = await response.json();
        setToken(data.token);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    getToken();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-gray-500">Connecting to interview...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  if (!token || !serverUrl) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-red-500">Missing token or server URL</p>
      </div>
    );
  }

  return (
    <LiveKitRoom
      video={false}
      audio={true}
      token={token}
      serverUrl={serverUrl}
      connect={true}
      onConnected={() => {
        console.log('Connected to LiveKit room');
        onConnect();
      }}
      onDisconnected={() => {
        console.log('Disconnected from LiveKit room');
        onDisconnect();
      }}
      onError={(error) => {
        console.error('LiveKit error:', error);
      }}
    >
      {/* RoomAudioRenderer automatically handles all audio track rendering */}
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}
