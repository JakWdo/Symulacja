import { Skeleton } from '../ui/skeleton';
import { Card, CardContent, CardHeader } from '../ui/card';
import logoImage from 'figma:asset/c69b7132bb4727fb2aee5acce0edc631b9d3e18f.png';

export function ResultsLoading() {
  return (
    <div className="space-y-6">
      {/* Generating message */}
      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="text-center py-12">
          <img 
            src={logoImage} 
            alt="sight logo" 
            className="w-12 h-12 mx-auto mb-4 animate-spin mix-blend-multiply dark:mix-blend-screen" 
          />
          <h3 className="text-foreground mb-2">Generating AI Summary</h3>
          <p className="text-muted-foreground mb-4">
            Analyzing responses and generating insights...
          </p>
          <p className="text-sm text-muted-foreground">
            Estimated time: ~30 seconds
          </p>
        </CardContent>
      </Card>

      {/* Skeleton preview */}
      <div className="space-y-6">
        <Card className="bg-card border border-border shadow-sm">
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <Skeleton className="h-6 w-40" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-48 w-full" />
            </CardContent>
          </Card>
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <Skeleton className="h-6 w-40" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-48 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
