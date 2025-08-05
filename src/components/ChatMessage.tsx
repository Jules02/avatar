import React from 'react';
import { Message } from './ChatInterface';
import { CheckCircle, AlertCircle, Lightbulb, Calendar, Sun } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  
  const getMessageIcon = () => {
    switch (message.type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-success" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      case 'suggestion':
        return <Lightbulb className="h-4 w-4 text-accent" />;
      case 'confirmation':
        return <Calendar className="h-4 w-4 text-primary" />;
      default:
        return null;
    }
  };

  const getMessageBorderColor = () => {
    switch (message.type) {
      case 'success':
        return 'border-l-success';
      case 'error':
        return 'border-l-destructive';
      case 'suggestion':
        return 'border-l-accent';
      case 'confirmation':
        return 'border-l-primary';
      default:
        return 'border-l-transparent';
    }
  };

  return (
    <div className={cn(
      "flex w-full animate-slide-up",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-3 shadow-sm border-l-4",
        isUser 
          ? "bg-primary text-primary-foreground ml-12" 
          : cn(
              "bg-card text-card-foreground mr-12 border",
              getMessageBorderColor()
            )
      )}>
        {/* Message header for assistant messages */}
        {!isUser && message.type && (
          <div className="flex items-center space-x-2 mb-2 pb-2 border-b border-border/50">
            {getMessageIcon()}
            <span className="text-xs font-medium text-muted-foreground capitalize">
              {message.type === 'confirmation' ? 'Needs Confirmation' : message.type}
            </span>
          </div>
        )}
        
        {/* Message content */}
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.text}
        </div>
        
        {/* Timestamp */}
        <div className={cn(
          "text-xs mt-2 pt-2 border-t border-opacity-20",
          isUser 
            ? "text-primary-foreground/70 border-primary-foreground/20" 
            : "text-muted-foreground border-border/50"
        )}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};