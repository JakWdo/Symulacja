import { Badge } from '@/components/ui/badge';
import { Clock } from 'lucide-react';

interface DataFreshnessBadgeProps {
  timestamp: string;
}

/**
 * DataFreshnessBadge - wyświetla badge ze świeżością danych persony.
 *
 * Kolory:
 * - <24h: zielony (fresh)
 * - 1-7 dni: żółty (recent)
 * - >7 dni: czerwony/warning (stale)
 */
export function DataFreshnessBadge({ timestamp }: DataFreshnessBadgeProps) {
  const getDaysDiff = (dateString: string): number => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  };

  const formatFreshness = (days: number): string => {
    if (days === 0) return 'Dzisiaj';
    if (days === 1) return 'Wczoraj';
    if (days < 7) return `${days} dni temu`;
    if (days < 30) return `${Math.floor(days / 7)} tyg. temu`;
    return `${Math.floor(days / 30)} mies. temu`;
  };

  const getVariant = (days: number): 'default' | 'secondary' | 'destructive' => {
    if (days < 1) return 'default';  // <24h - zielony (default w niektórych theme)
    if (days < 7) return 'secondary';  // 1-7 dni - szary/neutral
    return 'destructive';  // >7 dni - czerwony
  };

  const days = getDaysDiff(timestamp);
  const label = formatFreshness(days);
  const variant = getVariant(days);

  return (
    <Badge variant={variant} className="gap-1.5 whitespace-nowrap">
      <Clock className="w-3 h-3" />
      <span className="text-xs">{label}</span>
    </Badge>
  );
}
