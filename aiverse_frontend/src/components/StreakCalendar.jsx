import React from 'react';
import { Flame, Calendar } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const StreakCalendar = ({ 
  streakData = {}, 
  currentStreak = 0, 
  longestStreak = 0,
  isLoading = false 
}) => {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
  const daysInMonth = endOfMonth.getDate();
  const startDay = startOfMonth.getDay();

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const getActivityLevel = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    const activity = streakData[dateStr];
    if (!activity) return 0;
    if (activity >= 5) return 4;
    if (activity >= 3) return 3;
    if (activity >= 2) return 2;
    return 1;
  };

  const getActivityColor = (level) => {
    switch (level) {
      case 4: return 'bg-green-500';
      case 3: return 'bg-green-400';
      case 2: return 'bg-green-300';
      case 1: return 'bg-green-200';
      default: return 'bg-muted';
    }
  };

  const renderCalendarDays = () => {
    const days = [];
    
    // Empty cells for days before start of month
    for (let i = 0; i < startDay; i++) {
      days.push(<div key={`empty-${i}`} className="w-8 h-8" />);
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(today.getFullYear(), today.getMonth(), day);
      const isToday = day === today.getDate();
      const level = getActivityLevel(date);
      
      days.push(
        <div
          key={day}
          className={`
            w-8 h-8 rounded-md flex items-center justify-center text-xs font-medium
            transition-all hover:scale-110 cursor-default
            ${getActivityColor(level)}
            ${isToday ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}
            ${level === 0 ? 'text-muted-foreground' : 'text-green-900'}
          `}
          title={`${monthNames[today.getMonth()]} ${day}: ${level > 0 ? `${level} activities` : 'No activity'}`}
        >
          {day}
        </div>
      );
    }
    
    return days;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary" />
            Activity Calendar
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="grid grid-cols-7 gap-1">
              {Array.from({ length: 35 }).map((_, i) => (
                <div key={i} className="w-8 h-8 bg-muted rounded-md" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Calendar className="h-5 w-5 text-primary" />
            {monthNames[today.getMonth()]} {today.getFullYear()}
          </CardTitle>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Flame className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium">{currentStreak} day streak</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Day labels */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="w-8 h-6 text-center text-xs text-muted-foreground font-medium">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {renderCalendarDays()}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Less</span>
            <div className="flex gap-1">
              {[0, 1, 2, 3, 4].map((level) => (
                <div
                  key={level}
                  className={`w-4 h-4 rounded-sm ${getActivityColor(level)}`}
                />
              ))}
            </div>
            <span className="text-xs text-muted-foreground">More</span>
          </div>
          
          <div className="text-sm text-muted-foreground">
            Best: <span className="font-medium text-foreground">{longestStreak} days</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StreakCalendar;
