import { Inbox } from 'lucide-react';

export default function EmptyState({ 
  icon: Icon = Inbox,
  title = 'No data found',
  message = 'There is nothing to display here yet.',
  action
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
        <Icon className="w-8 h-8 text-muted-foreground" />
      </div>
      <div>
        <h3 className="font-serif text-lg font-medium text-foreground mb-1">{title}</h3>
        <p className="text-sm text-muted-foreground max-w-md">{message}</p>
      </div>
      {action}
    </div>
  );
}