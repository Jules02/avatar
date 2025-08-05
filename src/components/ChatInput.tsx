import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Mic } from 'lucide-react';
import { VoiceInput } from './VoiceInput';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-center space-x-3">
        <div className="flex-1 relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your leave request or click the mic to speak..."
            className="w-full resize-none rounded-2xl border border-border bg-background px-4 py-3 pr-16 text-sm placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200 min-h-[52px] max-h-32"
            rows={1}
            style={{
              height: 'auto',
              minHeight: '52px'
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 128) + 'px';
            }}
          />
          
          {/* Voice input button */}
          <VoiceInput 
            onTranscript={(transcript) => setMessage(transcript)}
            isEnabled={true}
          />
        </div>
        
        <Button
          type="submit"
          disabled={!message.trim()}
          className="h-12 w-12 rounded-2xl p-0 bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
      
      {/* Quick suggestions */}
      <div className="mt-3 flex flex-wrap gap-2">
        {[
          "I want to take tomorrow off",
          "Book me a long weekend",
          "Check my remaining vacation days",
          "I need Friday off for an appointment"
        ].map((suggestion, index) => (
          <Button
            key={index}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setMessage(suggestion)}
            className="text-xs rounded-full border-border/50 hover:border-primary hover:text-primary transition-colors"
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </form>
  );
};