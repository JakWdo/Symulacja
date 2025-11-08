import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Target } from 'lucide-react';
import { RecommendationItem } from './RecommendationItem';

interface StrategicRecommendationsCardProps {
  recommendations: string[];
  className?: string;
}

/**
 * Karta z rekomendacjami strategicznymi
 */
export const StrategicRecommendationsCard: React.FC<StrategicRecommendationsCardProps> = ({
  recommendations,
  className = '',
}) => {
  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  // Automatycznie przypisz priority based na pozycji (pierwsze 2 = high, kolejne 2 = medium, reszta = low)
  const getAutoPriority = (index: number): 'high' | 'medium' | 'low' => {
    if (index < 2) return 'high';
    if (index < 4) return 'medium';
    return 'low';
  };

  return (
    <Card className={`bg-card border border-border shadow-sm ${className}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-success" />
          <CardTitle className="text-card-foreground font-crimson text-xl">
            Rekomendacje Strategiczne
          </CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          Działania rekomendowane na podstawie analizy
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recommendations.map((recommendation, index) => (
            <RecommendationItem
              key={index}
              recommendation={recommendation}
              priority={getAutoPriority(index)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
