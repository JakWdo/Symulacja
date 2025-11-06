import { AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';

interface ResultsErrorProps {
  error: string;
  onRetry?: () => void;
}

export function ResultsError({ error, onRetry }: ResultsErrorProps) {
  return (
    <div className="bg-card border border-border rounded-lg shadow-sm p-6">
      <Alert variant="destructive" className="mb-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="ml-2">
          {error || 'An error occurred while generating the AI summary.'}
        </AlertDescription>
      </Alert>

      <div className="text-center py-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10 mb-6">
          <AlertCircle className="w-8 h-8 text-destructive" />
        </div>
        <h3 className="text-foreground mb-2">Generation Failed</h3>
        <p className="text-muted-foreground max-w-md mx-auto mb-8">
          We encountered an issue while generating the AI summary. Please try again or contact support if the problem persists.
        </p>
        
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">Next steps:</p>
          <ul className="text-sm text-muted-foreground space-y-1 text-left max-w-sm mx-auto">
            <li>• Check your internet connection</li>
            <li>• Verify that the discussion completed successfully</li>
            <li>• Try regenerating the summary</li>
            <li>• Contact support if the issue continues</li>
          </ul>
        </div>

        {onRetry && (
          <Button 
            onClick={onRetry}
            className="mt-8 bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
}
