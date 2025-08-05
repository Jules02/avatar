import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Calendar, TrendingDown, Clock, Gift } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LeaveBalanceTrackerProps {
  totalDays: number;
  usedDays: number;
  pendingDays: number;
  className?: string;
}

export const LeaveBalanceTracker: React.FC<LeaveBalanceTrackerProps> = ({
  totalDays,
  usedDays,
  pendingDays,
  className
}) => {
  const remainingDays = totalDays - usedDays - pendingDays;
  const usedPercentage = (usedDays / totalDays) * 100;
  const pendingPercentage = (pendingDays / totalDays) * 100;
  const remainingPercentage = (remainingDays / totalDays) * 100;

  const getStatusColor = () => {
    if (remainingPercentage > 50) return 'text-success';
    if (remainingPercentage > 20) return 'text-accent';
    return 'text-destructive';
  };

  const getStatusMessage = () => {
    if (remainingPercentage > 50) return 'Great balance!';
    if (remainingPercentage > 20) return 'Plan ahead';
    return 'Consider planning';
  };

  return (
    <div className={cn("space-y-4 p-4 border border-border rounded-lg bg-card", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Calendar className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-foreground">Leave Balance</h3>
        </div>
        <Badge variant="outline" className={getStatusColor()}>
          {getStatusMessage()}
        </Badge>
      </div>

      {/* Progress visualization */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Usage Progress</span>
          <span>{usedDays + pendingDays}/{totalDays} days</span>
        </div>
        
        <div className="relative">
          <Progress 
            value={usedPercentage + pendingPercentage} 
            className="h-3 bg-muted"
          />
          <Progress 
            value={usedPercentage} 
            className="absolute top-0 h-3 bg-transparent"
            style={{
              background: 'hsl(var(--success))'
            }}
          />
        </div>
        
        <div className="flex justify-between items-center text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-success"></div>
            <span className="text-muted-foreground">Used: {usedDays}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-accent"></div>
            <span className="text-muted-foreground">Pending: {pendingDays}</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-muted"></div>
            <span className="text-muted-foreground">Remaining: {remainingDays}</span>
          </div>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border">
        <div className="text-center space-y-1">
          <TrendingDown className="h-4 w-4 mx-auto text-muted-foreground" />
          <div className="text-xs text-muted-foreground">This Month</div>
          <div className="text-sm font-medium">{Math.max(0, usedDays - 8)} days</div>
        </div>
        <div className="text-center space-y-1">
          <Clock className="h-4 w-4 mx-auto text-muted-foreground" />
          <div className="text-xs text-muted-foreground">Avg/Month</div>
          <div className="text-sm font-medium">{(totalDays / 12).toFixed(1)} days</div>
        </div>
        <div className="text-center space-y-1">
          <Gift className="h-4 w-4 mx-auto text-muted-foreground" />
          <div className="text-xs text-muted-foreground">Expires</div>
          <div className="text-sm font-medium">Dec 31</div>
        </div>
      </div>
    </div>
  );
};