import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Calendar, 
  Sun, 
  Briefcase, 
  Heart, 
  Plane, 
  Clock, 
  Coffee,
  Home,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  template: string;
  color: string;
  popular?: boolean;
}

interface QuickActionsPanelProps {
  onActionSelect: (template: string) => void;
  className?: string;
}

const quickActions: QuickAction[] = [
  {
    id: 'sick-day',
    title: 'Sick Day',
    description: 'Quick sick leave request',
    icon: <Heart className="h-4 w-4" />,
    template: "I need to take a sick day today. I'm not feeling well and will rest to recover quickly.",
    color: 'text-destructive',
    popular: true
  },
  {
    id: 'long-weekend',
    title: 'Long Weekend',
    description: 'Extend your weekend',
    icon: <Sun className="h-4 w-4" />,
    template: "I'd like to take Friday off to create a long weekend. Please check if this works with the team schedule.",
    color: 'text-accent',
    popular: true
  },
  {
    id: 'vacation',
    title: 'Vacation',
    description: 'Plan your holidays',
    icon: <Plane className="h-4 w-4" />,
    template: "I'm planning a vacation and would like to book time off. Could you help me find the best dates based on my team's schedule?",
    color: 'text-primary'
  },
  {
    id: 'appointment',
    title: 'Medical Appointment',
    description: 'Doctor or dental visit',
    icon: <Clock className="h-4 w-4" />,
    template: "I have a medical appointment and need a few hours off. Can you help me determine the best time with minimal impact?",
    color: 'text-secondary'
  },
  {
    id: 'mental-health',
    title: 'Mental Health Day',
    description: 'Take care of yourself',
    icon: <Coffee className="h-4 w-4" />,
    template: "I'd like to take a mental health day to recharge. When would be the best day this week with the lightest workload?",
    color: 'text-success'
  },
  {
    id: 'family',
    title: 'Family Time',
    description: 'Important family events',
    icon: <Home className="h-4 w-4" />,
    template: "I have an important family event coming up and need time off. Can you suggest the best days and handle the booking?",
    color: 'text-accent'
  },
  {
    id: 'emergency',
    title: 'Emergency Leave',
    description: 'Urgent situations',
    icon: <Zap className="h-4 w-4" />,
    template: "I have an emergency situation and need immediate time off. Please process this as urgent and notify my team.",
    color: 'text-destructive',
    popular: true
  },
  {
    id: 'work-life',
    title: 'Work-Life Balance',
    description: 'Regular breaks',
    icon: <Briefcase className="h-4 w-4" />,
    template: "I'd like to take some time off to maintain work-life balance. What are my options for the coming weeks?",
    color: 'text-primary'
  }
];

export const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({
  onActionSelect,
  className
}) => {
  return (
    <div className={cn("space-y-4 p-4 border border-border rounded-lg bg-card", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Zap className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-foreground">Quick Actions</h3>
        </div>
        <Badge variant="secondary" className="text-xs">
          {quickActions.filter(a => a.popular).length} Popular
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {quickActions.map((action) => (
          <Button
            key={action.id}
            variant="outline"
            className={cn(
              "h-auto p-3 justify-start text-left hover:bg-muted/50 transition-all duration-200 group",
              "border-border/50 hover:border-primary/50 w-full"
            )}
            onClick={() => onActionSelect(action.template)}
          >
            <div className="flex items-start space-x-3 w-full min-w-0">
              <div className={cn("mt-0.5 transition-colors group-hover:scale-110 flex-shrink-0", action.color)}>
                {action.icon}
              </div>
              <div className="flex-1 min-w-0 overflow-hidden">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className="font-medium text-sm text-foreground group-hover:text-primary transition-colors truncate">
                    {action.title}
                  </h4>
                  {action.popular && (
                    <Badge variant="secondary" className="text-xs px-1.5 py-0.5 flex-shrink-0">
                      Popular
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {action.description}
                </p>
              </div>
            </div>
          </Button>
        ))}
      </div>

      <div className="pt-3 border-t border-border">
        <p className="text-xs text-muted-foreground text-center">
          Click any action to quickly fill the message field with a template
        </p>
      </div>
    </div>
  );
};