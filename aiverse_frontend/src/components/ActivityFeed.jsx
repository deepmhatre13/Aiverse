import React from 'react';
import { 
  CheckCircle2, 
  BookOpen, 
  MessageSquare, 
  Trophy, 
  Code,
  Flame,
  Star,
  Clock
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

const ActivityFeed = ({ activities = [], isLoading = false, maxHeight = '400px' }) => {
  const getActivityIcon = (type) => {
    const iconMap = {
      submission: <Code className="h-4 w-4" />,
      course_complete: <BookOpen className="h-4 w-4" />,
      lesson_complete: <CheckCircle2 className="h-4 w-4" />,
      discussion: <MessageSquare className="h-4 w-4" />,
      achievement: <Trophy className="h-4 w-4" />,
      streak: <Flame className="h-4 w-4" />,
      rank_up: <Star className="h-4 w-4" />,
    };
    return iconMap[type] || <Clock className="h-4 w-4" />;
  };

  const getActivityColor = (type) => {
    const colorMap = {
      submission: 'bg-primary/10 text-primary border-primary/20',
      course_complete: 'bg-green-500/10 text-green-500 border-green-500/20',
      lesson_complete: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      discussion: 'bg-primary/10 text-primary border-primary/20',
      achievement: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
      streak: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
      rank_up: 'bg-primary/10 text-primary border-primary/20',
    };
    return colorMap[type] || 'bg-muted text-muted-foreground border-border';
  };

  // Transform API data to component format
  const displayActivities = activities.map((activity, index) => {
    if (activity.type === 'submission') {
      return {
        id: activity.submission_id || index,
        type: 'submission',
        title: activity.status === 'ACCEPTED' ? 'Accepted submission' : 'Submitted solution',
        description: activity.problem_title || activity.problem_slug || 'Problem',
        score: activity.score,
        timestamp: activity.created_at ? new Date(activity.created_at) : new Date(),
      };
    } else if (activity.type === 'lesson') {
      return {
        id: index,
        type: 'lesson_complete',
        title: 'Completed lesson',
        description: activity.title || 'Lesson',
        timestamp: activity.created_at ? new Date(activity.created_at) : new Date(),
      };
    }
    return {
      id: index,
      type: activity.type || 'submission',
      title: activity.title || 'Activity',
      description: activity.description || '',
      timestamp: activity.created_at ? new Date(activity.created_at) : new Date(),
    };
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex gap-3 animate-pulse">
                <div className="h-10 w-10 rounded-full bg-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-3/4" />
                  <div className="h-3 bg-muted rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Clock className="h-5 w-5 text-primary" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        {displayActivities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No recent activity. Start solving problems to see your progress here!</p>
          </div>
        ) : (
          <ScrollArea style={{ height: maxHeight }}>
            <div className="space-y-4 pr-4">
              {displayActivities.map((activity, index) => (
              <div 
                key={activity.id || index}
                className="flex gap-3 group"
              >
                <div className={`
                  flex-shrink-0 w-10 h-10 rounded-full border flex items-center justify-center
                  transition-transform group-hover:scale-110
                  ${getActivityColor(activity.type)}
                `}>
                  {getActivityIcon(activity.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium text-sm truncate">
                      {activity.title}
                    </p>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {activity.timestamp 
                        ? formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })
                        : 'Recently'
                      }
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground truncate">
                    {activity.description}
                  </p>
                  {activity.score !== undefined && (
                    <p className="text-sm font-mono text-green-500 mt-1">
                      Score: {activity.score.toFixed(4)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

export default ActivityFeed;
