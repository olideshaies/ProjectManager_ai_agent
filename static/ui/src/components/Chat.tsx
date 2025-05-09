import React, { useState, useRef, useEffect } from 'react';

// Message structure
interface Message {
  type: 'user' | 'system';
  content: string;
  timestamp: string;
}

export const Chat: React.FC = () => {
  const [status, setStatus] = useState('Idle');
  const [recording, setRecording] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Add message to history
  const addMessage = (type: 'user' | 'system', content: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setMessages(prev => [...prev, { type, content, timestamp }]);
  };

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ Microphone stream acquired:', stream);
      // Try a known-compatible MIME type first
      let options: MediaRecorderOptions = { mimeType: 'audio/webm; codecs=opus' };
      if (!MediaRecorder.isTypeSupported(options.mimeType || '')) {
        console.warn(`MIME type ${options.mimeType} not supported, using default`);
        options = {};
      }
      const mr = new MediaRecorder(stream, options);
      console.log('🎙️ MediaRecorder created, mimeType:', mr.mimeType);
      mediaRecorderRef.current = mr;
      audioChunksRef.current = [];
      // Attach event handlers before starting
      mr.ondataavailable = e => {
        console.log('📦 dataavailable event, size:', e.data.size);
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mr.onstop = onStopRecording;
      mr.start();
      console.log('▶️ Recording started');
      setRecording(true);
      setStatus('Recording...');
    } catch (err: any) {
      console.error(err);
      setStatus('Error accessing microphone');
      addMessage('system', `Error: ${err.message}`);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      setStatus('Stopped recording.');
    }
  };

  // Handler when recording stops
  const onStopRecording = async () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'voice_command.wav');
    setStatus('Uploading audio...');

    try {
      const res = await fetch('/voice/command', { method: 'POST', body: formData });
      const result = await res.json();
      addMessage('user', `Command: ${result.transcription}`);
      addMessage('system', `Response: ${result.message}`);
      setStatus('Command processed successfully');
    } catch (err: any) {
      console.error(err);
      setStatus('Error processing command');
      addMessage('system', `Error: ${err.message}`);
    }
  };

  return (
    <div className="chat-container">
      <h2>Voice Command Chat</h2>
      <div>
        <button onClick={startRecording} disabled={recording}>Record Command</button>
        <button onClick={stopRecording} disabled={!recording}>Stop Recording</button>
        <span style={{ marginLeft: '1rem' }}>{status}</span>
      </div>
      <div className="conversation-container" style={{ maxHeight: '300px', overflowY: 'auto', marginTop: '1rem' }}>
        {messages.map((m, i) => (
          <div key={i} style={{ margin: '0.5rem 0', padding: '0.5rem', borderRadius: '4px', backgroundColor: m.type === 'user' ? '#e3f2fd' : '#f5f5f5' }}>
            <div style={{ fontSize: '0.8em', color: '#666' }}>{m.timestamp}</div>
            <div>{m.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}; 