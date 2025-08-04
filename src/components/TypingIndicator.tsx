import React from 'react';
import { cn } from '@/lib/utils';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start animate-slide-up">
      <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-card text-card-foreground mr-12 border border-border/50 shadow-sm">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="h-2 w-2 bg-muted-foreground rounded-full animate-pulse-typing"></div>
            <div className="h-2 w-2 bg-muted-foreground rounded-full animate-pulse-typing" style={{ animationDelay: '0.2s' }}></div>
            <div className="h-2 w-2 bg-muted-foreground rounded-full animate-pulse-typing" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <span className="text-xs text-muted-foreground">Assistant is typing...</span>
        </div>
      </div>
    </div>
  );
};