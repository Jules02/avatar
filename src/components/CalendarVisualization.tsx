import React, { useState } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  Calendar as CalendarIcon, 
  Users, 
  Sun, 
  CloudRain, 
  Briefcase,
  ChevronLeft,
  ChevronRight 
} from 'lucide-react';
import { format, addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval } from 'date-fns';
import { cn } from '@/lib/utils';

interface CalendarEvent {
  date: Date;
  type: 'leave' | 'holiday' | 'busy' | 'conflict' | 'weather-good' | 'weather-bad';
  title: string;
  users?: string[];
}

interface CalendarVisualizationProps {
  onDateSelect?: (date: Date) => void;
  className?: string;
}

// Mock data for demonstration
const mockEvents: CalendarEvent[] = [
  { date: new Date(2024, 7, 2), type: 'leave', title: 'Your Leave', users: ['You'] },
  { date: new Date(2024, 7, 5), type: 'holiday', title: 'Public Holiday' },
  { date: new Date(2024, 7, 9), type: 'conflict', title: 'Team Meeting', users: ['Alice', 'Bob'] },
  { date: new Date(2024, 7, 15), type: 'leave', title: 'Team Leave', users: ['Charlie', 'Diana'] },
  { date: new Date(2024, 7, 22), type: 'weather-good', title: 'Sunny Day' },
  { date: new Date(2024, 7, 28), type: 'busy', title: 'Project Deadline' },
];

export const CalendarVisualization: React.FC<CalendarVisualizationProps> = ({
  onDateSelect,
  className
}) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>();

  const getEventForDate = (date: Date) => {
    return mockEvents.find(event => 
      event.date.toDateString() === date.toDateString()
    );
  };

  const getDayClassName = (date: Date) => {
    const event = getEventForDate(date);
    if (!event) return '';

    switch (event.type) {
      case 'leave':
        return 'bg-primary/20 text-primary hover:bg-primary/30';
      case 'holiday':
        return 'bg-accent/20 text-accent hover:bg-accent/30';
      case 'busy':
        return 'bg-destructive/20 text-destructive hover:bg-destructive/30';
      case 'conflict':
        return 'bg-orange-500/20 text-orange-600 hover:bg-orange-500/30';
      case 'weather-good':
        return 'bg-success/20 text-success hover:bg-success/30';
      case 'weather-bad':
        return 'bg-muted/40 text-muted-foreground hover:bg-muted/60';
      default:
        return '';
    }
  };

  const handleDateSelect = (date: Date | undefined) => {
    if (date) {
      setSelectedDate(date);
      onDateSelect?.(date);
    }
  };

  const goToPreviousMonth = () => {
    setCurrentMonth(subMonths(currentMonth, 1));
  };

  const goToNextMonth = () => {
    setCurrentMonth(addMonths(currentMonth, 1));
  };

  const selectedEvent = selectedDate ? getEventForDate(selectedDate) : null;

  return (
    <div className={cn("space-y-4 p-4 border border-border rounded-lg bg-card", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <CalendarIcon className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-foreground">Calendar Overview</h3>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={goToPreviousMonth}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium min-w-[120px] text-center">
            {format(currentMonth, 'MMMM yyyy')}
          </span>
          <Button variant="outline" size="sm" onClick={goToNextMonth}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Calendar
        mode="single"
        selected={selectedDate}
        onSelect={handleDateSelect}
        month={currentMonth}
        onMonthChange={setCurrentMonth}
        className="rounded-md border"
        modifiers={{
          booked: (date) => getEventForDate(date)?.type === 'leave',
          holiday: (date) => getEventForDate(date)?.type === 'holiday',
          busy: (date) => getEventForDate(date)?.type === 'busy',
          conflict: (date) => getEventForDate(date)?.type === 'conflict',
          good_weather: (date) => getEventForDate(date)?.type === 'weather-good',
        }}
        modifiersClassNames={{
          booked: getDayClassName(new Date()),
          holiday: getDayClassName(new Date()),
          busy: getDayClassName(new Date()),
          conflict: getDayClassName(new Date()),
          good_weather: getDayClassName(new Date()),
        }}
        components={{
          DayContent: ({ date }) => {
            const event = getEventForDate(date);
            return (
              <div className="relative w-full h-full flex items-center justify-center">
                <span>{date.getDate()}</span>
                {event && (
                  <div className="absolute -bottom-0.5 left-1/2 transform -translate-x-1/2 w-1 h-1 rounded-full bg-current opacity-60" />
                )}
              </div>
            );
          }
        }}
      />

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded bg-primary/20"></div>
          <span>Your Leave</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded bg-accent/20"></div>
          <span>Holidays</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded bg-destructive/20"></div>
          <span>Busy Days</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded bg-orange-500/20"></div>
          <span>Conflicts</span>
        </div>
      </div>

      {/* Selected date info */}
      {selectedEvent && (
        <div className="p-3 bg-muted/50 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">{selectedEvent.title}</h4>
            <Badge variant="secondary" className="text-xs">
              {format(selectedDate!, 'MMM dd')}
            </Badge>
          </div>
          {selectedEvent.users && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              <span>{selectedEvent.users.join(', ')}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};