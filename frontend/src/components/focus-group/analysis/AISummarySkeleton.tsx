import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Loading skeleton dla AI Summary
 */
export const AISummarySkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Executive Summary Card */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <Skeleton className="h-6 w-64" />
          <Skeleton className="h-4 w-96 mt-2" />
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Executive Summary */}
          <div className="space-y-3">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-20 w-full" />
          </div>

          {/* Key Insights Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-3">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-16 w-full" />
              </div>
            ))}
          </div>

          {/* Segment Analysis */}
          <div className="space-y-3">
            <Skeleton className="h-5 w-40" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-32 w-full" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
