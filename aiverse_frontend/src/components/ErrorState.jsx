import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';

export default function ErrorState({ 
  title = 'Something went wrong',
  message = 'An error occurred. Please try again.',
  onRetry 
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
      <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
        <AlertCircle className="w-8 h-8 text-destructive" />
      </div>
      <div>
        <h3 className="font-serif text-lg font-medium text-foreground mb-1">{title}</h3>
        <p className="text-sm text-muted-foreground max-w-md">{message}</p>
      </div>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-2">
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}