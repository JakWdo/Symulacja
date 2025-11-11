import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface FocusGroupHeaderProps {
  name: string;
  status: string;
  questionsCount: number;
  participantsCount: number;
  onBack: () => void;
}

export function FocusGroupHeader({
  name,
  status,
  questionsCount,
  participantsCount,
  onBack,
}: FocusGroupHeaderProps) {
  const { t } = useTranslation('focusGroups');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-brand-muted text-brand dark:text-brand border-brand/30';
      case 'running':
        return 'bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/30';
      case 'pending':
        return 'bg-muted text-muted-foreground border-border';
      case 'failed':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return t('view.statusLabel.running');
      case 'completed':
        return t('view.statusLabel.completed');
      case 'pending':
        return t('view.statusLabel.pending');
      case 'failed':
        return t('view.statusLabel.failed');
      default:
        return status;
    }
  };

  return (
    <div className="flex items-center gap-4">
      <Button
        variant="ghost"
        onClick={onBack}
        className="text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        {t('view.backButton')}
      </Button>
      <div>
        <h1 className="text-4xl font-bold text-foreground mb-2">{name}</h1>
        <div className="flex items-center gap-3">
          <Badge className={getStatusColor(status)}>
            {getStatusText(status)}
          </Badge>
          <span className="text-muted-foreground">•</span>
          <span className="text-muted-foreground">{t('view.questionsCount', { count: questionsCount })}</span>
          <span className="text-muted-foreground">•</span>
          <span className="text-muted-foreground">{t('view.participantsCount', { count: participantsCount })}</span>
        </div>
      </div>
    </div>
  );
}
