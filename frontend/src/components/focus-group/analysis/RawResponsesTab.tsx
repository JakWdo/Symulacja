import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare } from 'lucide-react';
import { ResponseFilters } from './ResponseFilters';
import { ResponsesList } from './ResponsesList';
import { ResponsesSkeleton } from './ResponsesSkeleton';
import { useFocusGroupResponses } from '@/hooks/focus-group/useFocusGroupResponses';
import type { Persona } from '@/types';
import { useTranslation } from 'react-i18next';

interface RawResponsesTabProps {
  focusGroupId: string;
  personas: Persona[];
}

/**
 * Tab z surowymi odpowiedziami + filters
 */
export const RawResponsesTab: React.FC<RawResponsesTabProps> = ({
  focusGroupId,
  personas,
}) => {
  const { t } = useTranslation('focusGroups');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPersonaId, setSelectedPersonaId] = useState('all');
  const [selectedQuestionIndex, setSelectedQuestionIndex] = useState('all');

  const { data: responses, isLoading, error } = useFocusGroupResponses(focusGroupId);

  if (isLoading) {
    return <ResponsesSkeleton />;
  }

  if (error) {
    return (
      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="py-12 text-center">
          <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-card-foreground mb-2">
            {t('analysis.rawResponses.errorTitle')}
          </h3>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : t('analysis.rawResponses.errorUnknown')}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!responses || responses.questions.length === 0) {
    return (
      <Card className="bg-card border border-border shadow-sm">
        <CardContent className="py-12 text-center">
          <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-card-foreground mb-2">
            {t('analysis.rawResponses.emptyTitle')}
          </h3>
          <p className="text-sm text-muted-foreground">
            {t('analysis.rawResponses.emptyDescription')}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border border-border shadow-sm">
      <CardHeader>
        <CardTitle className="text-card-foreground">{t('analysis.rawResponses.title')}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {t('analysis.rawResponses.description')}
          {' '}
          <span className="font-medium text-card-foreground">
            ({t('analysis.rawResponses.totalResponses', { count: responses.total_responses })})
          </span>
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Filters */}
        <ResponseFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedPersonaId={selectedPersonaId}
          onPersonaChange={setSelectedPersonaId}
          selectedQuestionIndex={selectedQuestionIndex}
          onQuestionChange={setSelectedQuestionIndex}
          personas={personas}
          questions={responses.questions.map((q) => q.question)}
        />

        {/* Responses List */}
        <ResponsesList
          responses={responses}
          personas={personas}
          searchQuery={searchQuery}
          selectedPersonaId={selectedPersonaId}
          selectedQuestionIndex={selectedQuestionIndex}
        />
      </CardContent>
    </Card>
  );
};
