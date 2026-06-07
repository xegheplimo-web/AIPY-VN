import { useState, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface VoiceSearchProps {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

export function VoiceSearch({ onTranscript, onError, className = '' }: VoiceSearchProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        await uploadAudio(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      onError?.('Không thể truy cập microphone. Vui lòng cấp quyền.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const uploadAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');

      const response = await fetch('/api/chat/voice/search', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        onTranscript(data.text);
      } else {
        onError?.(data.message || 'Không thể chuyển đổi giọng nói.');
      }
    } catch (error) {
      console.error('Error uploading audio:', error);
      onError?.('Lỗi khi tải lên giọng nói.');
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <button
      onClick={toggleRecording}
      disabled={isProcessing}
      className={`
        p-3 rounded-full transition-all duration-200
        ${isRecording 
          ? 'bg-red-500 text-white animate-pulse' 
          : 'bg-blue-600 text-white hover:bg-blue-700'
        }
        ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
      title={isRecording ? 'Dừng ghi âm' : 'Bắt đầu ghi âm'}
    >
      {isProcessing ? (
        <Loader2 className="w-5 h-5 animate-spin" />
      ) : isRecording ? (
        <MicOff className="w-5 h-5" />
      ) : (
        <Mic className="w-5 h-5" />
      )}
    </button>
  );
}
