import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Loading skeleton dla Raw Responses
 */
export const ResponsesSkeleton: React.FC = () => {
  return (
    <Card className="bg-card border border-border shadow-sm">
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-80 mt-2" />
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Filters */}
        <div className="flex gap-3">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-48" />
        </div>

        {/* Response Cards */}
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="space-y-4">
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-12" />
              <Skeleton className="h-5 w-96" />
            </div>
            <div className="ml-12 space-y-3">
              {[1, 2].map((j) => (
                <div key={j} className="space-y-2">
                  <div className="flex items-center gap-3">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                  <Skeleton className="h-16 w-full ml-11" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
