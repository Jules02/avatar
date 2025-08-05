import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// Extend Window interface for Speech Recognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  isEnabled?: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, isEnabled = true }) => {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!isEnabled) return;

    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser');
      return;
    }

    const recognitionInstance = new SpeechRecognition();
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = false;
    recognitionInstance.lang = 'en-US';

    recognitionInstance.onstart = () => {
      setIsListening(true);
      setError('');
    };

    recognitionInstance.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
      setIsListening(false);
    };

    recognitionInstance.onerror = (event) => {
      setError(`Speech recognition error: ${event.error}`);
      setIsListening(false);
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };

    setRecognition(recognitionInstance);

    return () => {
      if (recognitionInstance) {
        recognitionInstance.abort();
      }
    };
  }, [isEnabled, onTranscript]);

  const startListening = () => {
    if (recognition && !isListening) {
      recognition.start();
    } else if (!recognition) {
      // Fallback for unsupported browsers
      alert('Speech recognition is not supported in this browser or preview environment.');
    }
  };

  const stopListening = () => {
    if (recognition && isListening) {
      recognition.stop();
    }
  };

  // Show button even if speech recognition is not supported
  const isSupported = !!recognition;
  const showError = error && isSupported;

  return (
    <Button
      type="button"
      variant={isListening ? "destructive" : "secondary"}
      size="sm"
      onClick={isListening ? stopListening : startListening}
      className={cn(
        "absolute right-3 top-1/2 transform -translate-y-1/2 h-10 w-10 p-0 transition-all duration-200 shadow-md",
        isListening 
          ? "animate-pulse shadow-destructive/25" 
          : "hover:shadow-lg hover:scale-105",
        !isSupported && "opacity-75"
      )}
      title={!isSupported ? "Speech recognition not supported in this environment" : isListening ? "Stop recording" : "Start voice input"}
    >
      {isListening ? (
        <div className="relative flex items-center justify-center">
          <MicOff className="h-5 w-5" />
          <div className="absolute -inset-2 rounded-full bg-background/20 animate-ping" />
        </div>
      ) : (
        <Mic className="h-5 w-5" />
      )}
    </Button>
  );
};