import React from 'react';
import { CheckCircle2, XCircle, Clock, ChevronDown, ChevronUp, Trophy } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';

const SubmissionHistory = ({ submissions = [], isLoading = false }) => {
  const [openId, setOpenId] = React.useState(null);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed':
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
      case 'error':
        return <XCircle className="h-4 w-4 text-destructive" />;
      case 'pending':
      case 'running':
        return <Clock className="h-4 w-4 text-yellow-500 animate-pulse" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'passed':
      case 'success':
        return <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/30">Passed</Badge>;
      case 'failed':
      case 'error':
        return <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/30">Failed</Badge>;
      case 'pending':
      case 'running':
        return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/30">Running</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="h-16 bg-muted rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  if (submissions.length === 0) {
    return (
      <div className="text-center py-8">
        <Trophy className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
        <p className="text-muted-foreground">No submissions yet</p>
        <p className="text-sm text-muted-foreground/70">
          Submit your solution to see it here
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {submissions.map((submission, index) => (
        <Collapsible
          key={submission.id || index}
          open={openId === (submission.id || index)}
          onOpenChange={(open) => setOpenId(open ? (submission.id || index) : null)}
        >
          <CollapsibleTrigger className="w-full">
            <div className={`
              flex items-center justify-between p-4 rounded-lg border transition-all
              hover:bg-muted/50 cursor-pointer
              ${openId === (submission.id || index) ? 'bg-muted/50' : 'bg-card'}
              ${submission.status === 'passed' || submission.status === 'success' 
                ? 'border-green-500/20' 
                : 'border-border'
              }
            `}>
              <div className="flex items-center gap-4">
                {getStatusIcon(submission.status)}
                <div className="text-left">
                  <p className="font-medium text-sm">
                    Submission #{submissions.length - index}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {submission.created_at 
                      ? formatDistanceToNow(new Date(submission.created_at), { addSuffix: true })
                      : 'Just now'
                    }
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                {submission.score !== undefined && (
                  <span className={`
                    font-mono font-bold
                    ${(submission.status === 'passed' || submission.status === 'success')
                      ? 'text-green-500' 
                      : 'text-muted-foreground'
                    }
                  `}>
                    {typeof submission.score === 'number' 
                      ? submission.score.toFixed(4) 
                      : submission.score
                    }
                  </span>
                )}
                {getStatusBadge(submission.status)}
                {openId === (submission.id || index) 
                  ? <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  : <ChevronDown className="h-4 w-4 text-muted-foreground" />
                }
              </div>
            </div>
          </CollapsibleTrigger>
          
          <CollapsibleContent>
            <div className="mt-2 p-4 bg-muted/30 rounded-lg border border-border space-y-3">
              {submission.public_score !== undefined && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Public Score</span>
                  <span className="font-mono">{submission.public_score}</span>
                </div>
              )}
              {submission.private_score !== undefined && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Private Score</span>
                  <span className="font-mono">{submission.private_score}</span>
                </div>
              )}
              {submission.metric && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Metric</span>
                  <span className="font-mono uppercase">{submission.metric}</span>
                </div>
              )}
              {submission.execution_time && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Execution Time</span>
                  <span className="font-mono">{submission.execution_time}s</span>
                </div>
              )}
              {submission.error && (
                <div className="p-3 bg-destructive/10 rounded-lg border border-destructive/20">
                  <p className="text-sm text-destructive font-mono">{submission.error}</p>
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  );
};

export default SubmissionHistory;
