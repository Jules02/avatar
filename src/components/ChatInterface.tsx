import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { LeaveBalanceTracker } from './LeaveBalanceTracker';
import { CalendarVisualization } from './CalendarVisualization';
import { QuickActionsPanel } from './QuickActionsPanel';
import { CollaborationPanel } from './CollaborationPanel';
import { ThemeToggle } from './ThemeToggle';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar, Sun, AlertCircle, Zap, Users, Settings, Menu, X } from 'lucide-react';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  type?: 'confirmation' | 'suggestion' | 'error' | 'success';
}

const mockResponses = [
  {
    triggers: ['friday', 'weather', 'sunny'],
    response: "I understand you'd like to take Friday off if the weather is sunny! Let me check the weather forecast and your available days off. 🌤️\n\nYou currently have 12 vacation days remaining. Would you like me to provisionally book Friday and automatically confirm if the weather forecast shows sun?",
    type: 'confirmation' as const
  },
  {
    triggers: ['two days', 'next week', 'public holiday'],
    response: "I'll help you book two days off next week, avoiding any public holidays! 📅\n\nNext week looks good - no public holidays scheduled. Your best options are:\n• Monday & Tuesday (weather looks great!)\n• Wednesday & Thursday (lighter workload)\n\nWhich days would you prefer?",
    type: 'suggestion' as const
  },
  {
    triggers: ['sick', 'emergency', 'urgent'],
    response: "I understand this is urgent. I'll process your emergency leave request immediately. 🚨\n\nYour request has been escalated to HR for fast-track approval. You should receive confirmation within 30 minutes.",
    type: 'success' as const
  }
];

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hi! I'm your AI-powered leave booking assistant. I can help you request time off using natural language, check team availability, suggest optimal dates, and much more! Try saying something like 'I want to take Friday off' or explore the panels on the right. 🏖️✨",
      sender: 'assistant',
      timestamp: new Date(),
      type: 'suggestion'
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    // Simulate assistant response
    setTimeout(() => {
      let response = "I'd be happy to help you with your leave request! Could you provide more details about the dates you'd like to take off?";
      let responseType: Message['type'] = undefined;

      // Check for matching triggers
      const lowerText = text.toLowerCase();
      const matchingResponse = mockResponses.find(mock => 
        mock.triggers.some(trigger => lowerText.includes(trigger))
      );

      if (matchingResponse) {
        response = matchingResponse.response;
        responseType = matchingResponse.type;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response,
        sender: 'assistant',
        timestamp: new Date(),
        type: responseType
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleSuggestBestDays = () => {
    const suggestion = "🤖 **AI Analysis Complete** - Here are the smartest leave options based on weather, team schedule, and workload:\n\n🌞 **This Friday** - 89% optimal (sunny weather, light workload, only 2 team members off)\n📅 **Next Monday** - 94% optimal (long weekend opportunity, minimal conflicts)\n🌴 **Week of March 15th** - 97% optimal (spring break season, perfect weather, team availability high)\n\n*Smart tip: Booking Monday gives you a 4-day weekend with minimal PTO usage!*\n\nShall I proceed with any of these recommendations?";
    
    const assistantMessage: Message = {
      id: Date.now().toString(),
      text: suggestion,
      sender: 'assistant',
      timestamp: new Date(),
      type: 'suggestion'
    };

    setMessages(prev => [...prev, assistantMessage]);
  };

  const handleQuickAction = (template: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      text: template,
      sender: 'user',
      timestamp: new Date()
    }]);
    
    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: "I've received your request and I'm analyzing the best options for you. Let me check team availability, workload patterns, and other factors to give you the optimal recommendation. ⚡",
        sender: 'assistant',
        timestamp: new Date(),
        type: 'confirmation'
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Main Chat Area */}
      <div className={`flex flex-col transition-all duration-300 ${sidebarOpen ? 'flex-1' : 'w-full'}`}>
        {/* Header */}
        <div className="border-b border-border bg-card px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-3">
                {/* Talan Logo */}
                <img 
                  src="/lovable-uploads/be788554-190f-402a-8634-16e344334b3f.png" 
                  alt="Talan" 
                  className="h-8 w-auto"
                />
                <div className="flex items-center space-x-2">
                  <Calendar className="h-6 w-6 text-primary" />
                  <h1 className="text-xl font-semibold text-foreground">AI Leave Assistant</h1>
                </div>
              </div>
              <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                <div className="h-2 w-2 bg-success rounded-full animate-pulse"></div>
                <span>AI Online</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSuggestBestDays}
                className="text-xs"
              >
                <Zap className="h-3 w-3 mr-1" />
                AI Suggestions
              </Button>
              <ThemeToggle />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="h-8 w-8 p-0"
              >
                {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isTyping && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border bg-card px-6 py-4">
          <ChatInput onSendMessage={handleSendMessage} />
        </div>
      </div>

      {/* Enhanced Sidebar */}
      {sidebarOpen && (
        <div className="w-96 border-l border-border bg-card/50 backdrop-blur-sm overflow-y-auto">
          <div className="p-4 space-y-4">
            {/* Leave Balance */}
            <LeaveBalanceTracker
              totalDays={25}
              usedDays={8}
              pendingDays={3}
            />

            {/* Tabs for different panels */}
            <Tabs defaultValue="calendar" className="w-full">
              <TabsList className="grid w-full grid-cols-3 h-11 p-1 bg-muted/30">
                <TabsTrigger value="calendar" className="text-sm font-medium px-3 py-2 data-[state=active]:bg-background data-[state=active]:shadow-sm transition-all">
                  <Calendar className="h-4 w-4 mr-2" />
                  <span className="hidden sm:inline">Calendar</span>
                  <span className="sm:hidden">Cal</span>
                </TabsTrigger>
                <TabsTrigger value="actions" className="text-sm font-medium px-3 py-2 data-[state=active]:bg-background data-[state=active]:shadow-sm transition-all">
                  <Zap className="h-4 w-4 mr-2" />
                  <span className="hidden sm:inline">Actions</span>
                  <span className="sm:hidden">Act</span>
                </TabsTrigger>
                <TabsTrigger value="team" className="text-sm font-medium px-3 py-2 data-[state=active]:bg-background data-[state=active]:shadow-sm transition-all">
                  <Users className="h-4 w-4 mr-2" />
                  <span className="hidden sm:inline">Team</span>
                  <span className="sm:hidden">Team</span>
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="calendar" className="mt-4">
                <CalendarVisualization 
                  onDateSelect={(date) => {
                    const message = `I'd like to take ${date.toLocaleDateString()} off. Can you check if this works with the team schedule?`;
                    handleSendMessage(message);
                  }}
                />
              </TabsContent>
              
              <TabsContent value="actions" className="mt-4">
                <QuickActionsPanel onActionSelect={handleQuickAction} />
              </TabsContent>
              
              <TabsContent value="team" className="mt-4">
                <CollaborationPanel />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      )}
    </div>
  );
};