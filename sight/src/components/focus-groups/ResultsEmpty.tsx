import { BarChart3 } from 'lucide-react';
import { Button } from '../ui/button';

interface ResultsEmptyProps {
  onStartDiscussion?: () => void;
}

export function ResultsEmpty({ onStartDiscussion }: ResultsEmptyProps) {
  return (
    <div className="bg-card border border-border rounded-lg shadow-sm">
      <div className="text-center py-20 px-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted mb-6">
          <BarChart3 className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-foreground mb-2">No Results Yet</h3>
        <p className="text-muted-foreground max-w-md mx-auto mb-8">
          Run the discussion simulation to generate analysis and insights. Configure your questions and participants first, then start the discussion.
        </p>
        {onStartDiscussion && (
          <Button 
            onClick={onStartDiscussion}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            Go to Discussion
          </Button>
        )}
      </div>
    </div>
  );
}
