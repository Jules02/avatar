import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  Users, 
  Clock, 
  Calendar,
  Dot,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface TeamMember {
  id: string;
  name: string;
  avatar?: string;
  status: 'online' | 'away' | 'offline';
  currentLeave?: {
    type: 'vacation' | 'sick' | 'personal';
    startDate: Date;
    endDate: Date;
    reason?: string;
  };
  upcomingLeave?: {
    type: 'vacation' | 'sick' | 'personal';
    startDate: Date;
    endDate: Date;
    approved: boolean;
  };
}

interface CollaborationPanelProps {
  className?: string;
}

// Mock data for demonstration
const mockTeamMembers: TeamMember[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    status: 'online',
    upcomingLeave: {
      type: 'vacation',
      startDate: new Date(2024, 7, 15),
      endDate: new Date(2024, 7, 22),
      approved: true
    }
  },
  {
    id: '2',
    name: 'Bob Smith',
    status: 'away',
    currentLeave: {
      type: 'sick',
      startDate: new Date(2024, 7, 1),
      endDate: new Date(2024, 7, 3),
      reason: 'Flu recovery'
    }
  },
  {
    id: '3',
    name: 'Charlie Davis',
    status: 'online',
    upcomingLeave: {
      type: 'personal',
      startDate: new Date(2024, 7, 10),
      endDate: new Date(2024, 7, 11),
      approved: false
    }
  },
  {
    id: '4',
    name: 'Diana Wilson',
    status: 'online'
  },
  {
    id: '5',
    name: 'Eve Brown',
    status: 'offline',
    upcomingLeave: {
      type: 'vacation',
      startDate: new Date(2024, 7, 25),
      endDate: new Date(2024, 8, 5),
      approved: true
    }
  }
];

export const CollaborationPanel: React.FC<CollaborationPanelProps> = ({
  className
}) => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>(mockTeamMembers);

  const getStatusColor = (status: TeamMember['status']) => {
    switch (status) {
      case 'online':
        return 'bg-success';
      case 'away':
        return 'bg-accent';
      case 'offline':
        return 'bg-muted-foreground';
      default:
        return 'bg-muted-foreground';
    }
  };

  const getLeaveTypeColor = (type: 'vacation' | 'sick' | 'personal') => {
    switch (type) {
      case 'vacation':
        return 'bg-primary/10 text-primary border-primary/20';
      case 'sick':
        return 'bg-destructive/10 text-destructive border-destructive/20';
      case 'personal':
        return 'bg-accent/10 text-accent border-accent/20';
      default:
        return 'bg-muted/10 text-muted-foreground border-muted/20';
    }
  };

  const formatDateRange = (start: Date, end: Date) => {
    const startMonth = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endMonth = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `${startMonth} - ${endMonth}`;
  };

  const onLeaveCount = teamMembers.filter(member => member.currentLeave).length;
  const upcomingLeaveCount = teamMembers.filter(member => member.upcomingLeave).length;
  const pendingApprovals = teamMembers.filter(member => 
    member.upcomingLeave && !member.upcomingLeave.approved
  ).length;

  return (
    <div className={cn("space-y-4 p-4 border border-border rounded-lg bg-card", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-foreground">Team Status</h3>
        </div>
        <div className="flex items-center space-x-2">
          {pendingApprovals > 0 && (
            <Badge variant="destructive" className="text-xs">
              {pendingApprovals} pending
            </Badge>
          )}
          <Badge variant="secondary" className="text-xs">
            {teamMembers.filter(m => m.status === 'online').length} online
          </Badge>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-2 p-3 bg-muted/30 rounded-lg">
        <div className="text-center">
          <div className="text-lg font-semibold text-foreground">{onLeaveCount}</div>
          <div className="text-xs text-muted-foreground">On Leave</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-foreground">{upcomingLeaveCount}</div>
          <div className="text-xs text-muted-foreground">Upcoming</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-foreground">{teamMembers.length - onLeaveCount}</div>
          <div className="text-xs text-muted-foreground">Available</div>
        </div>
      </div>

      {/* Team members list */}
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {teamMembers.map((member) => (
          <div
            key={member.id}
            className="flex items-center space-x-3 p-2 rounded-lg hover:bg-muted/30 transition-colors"
          >
            <div className="relative">
              <Avatar className="h-8 w-8">
                <AvatarImage src={member.avatar} />
                <AvatarFallback className="text-xs">
                  {member.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div 
                className={cn(
                  "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-background",
                  getStatusColor(member.status)
                )}
              />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-foreground truncate">
                  {member.name}
                </span>
                {member.currentLeave && (
                  <Badge variant="outline" className={cn("text-xs", getLeaveTypeColor(member.currentLeave.type))}>
                    On {member.currentLeave.type}
                  </Badge>
                )}
              </div>

              {member.currentLeave && (
                <div className="text-xs text-muted-foreground">
                  Until {member.currentLeave.endDate.toLocaleDateString()}
                  {member.currentLeave.reason && ` • ${member.currentLeave.reason}`}
                </div>
              )}

              {member.upcomingLeave && !member.currentLeave && (
                <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  <span>{formatDateRange(member.upcomingLeave.startDate, member.upcomingLeave.endDate)}</span>
                  {!member.upcomingLeave.approved && (
                    <AlertTriangle className="h-3 w-3 text-accent" />
                  )}
                </div>
              )}
            </div>

            <div className="text-xs text-muted-foreground capitalize">
              {member.status}
            </div>
          </div>
        ))}
      </div>

      {/* Insights */}
      <div className="pt-3 border-t border-border">
        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <TrendingUp className="h-3 w-3" />
          <span>Team capacity: 80% • Best days for leave: Mon-Wed</span>
        </div>
      </div>
    </div>
  );
};