import React from 'react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Persona } from '@/types';

interface ResponseFiltersProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  selectedPersonaId: string;
  onPersonaChange: (value: string) => void;
  selectedQuestionIndex: string;
  onQuestionChange: (value: string) => void;
  personas: Persona[];
  questions: string[];
  className?: string;
}

/**
 * Filtry dla Raw Responses (search + dropdowns)
 */
export const ResponseFilters: React.FC<ResponseFiltersProps> = ({
  searchQuery,
  onSearchChange,
  selectedPersonaId,
  onPersonaChange,
  selectedQuestionIndex,
  onQuestionChange,
  personas,
  questions,
  className = '',
}) => {
  const { t } = useTranslation('focusGroups');

  return (
    <div className={`flex flex-col md:flex-row gap-3 ${className}`}>
      {/* Search */}
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder={t('analysis.filters.searchPlaceholder')}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Persona Filter */}
      <Select value={selectedPersonaId} onValueChange={onPersonaChange}>
        <SelectTrigger className="w-full md:w-[200px]">
          <SelectValue placeholder={t('analysis.filters.allParticipants')} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t('analysis.filters.allParticipants')}</SelectItem>
          {personas.map((persona) => (
            <SelectItem key={persona.id} value={persona.id}>
              {persona.full_name || `Persona ${persona.id.slice(0, 8)}`}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Question Filter */}
      <Select value={selectedQuestionIndex} onValueChange={onQuestionChange}>
        <SelectTrigger className="w-full md:w-[200px]">
          <SelectValue placeholder={t('analysis.filters.allQuestions')} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t('analysis.filters.allQuestions')}</SelectItem>
          {questions.map((question, index) => (
            <SelectItem key={index} value={index.toString()}>
              {t('analysis.filters.questionLabel', { number: index + 1 })}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
