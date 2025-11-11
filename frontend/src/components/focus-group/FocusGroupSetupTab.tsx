import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { Persona } from '@/types';

interface FocusGroupSetupTabProps {
  questions: string[];
  selectedPersonaIds: string[];
  personas: Persona[];
  canModifyConfig: boolean;
  isSaving: boolean;
  newQuestion: string;
  onNewQuestionChange: (value: string) => void;
  onAddQuestion: () => void;
  onRemoveQuestion: (index: number) => void;
  onPersonaToggle: (personaId: string, checked: boolean) => void;
}

export function FocusGroupSetupTab({
  questions,
  selectedPersonaIds,
  personas,
  canModifyConfig,
  isSaving,
  newQuestion,
  onNewQuestionChange,
  onAddQuestion,
  onRemoveQuestion,
  onPersonaToggle,
}: FocusGroupSetupTabProps) {
  const { t } = useTranslation('focusGroups');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Questions */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="text-card-foreground">{t('view.setup.questionsTitle')}</CardTitle>
              <p className="text-muted-foreground">
                {canModifyConfig
                  ? t('view.setup.questionsDescriptionEditable')
                  : t('view.setup.questionsDescriptionReadonly')}
              </p>
            </div>
            {isSaving && (
              <Badge variant="outline" className="text-xs">
                {t('view.setup.saving')}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {questions.map((question: string, index: number) => (
              <div key={index} className="p-3 bg-muted rounded-lg border border-border">
                <div className="flex items-start gap-3">
                  <span className="text-sm font-medium text-brand bg-brand-muted px-2 py-1 rounded">
                    Q{index + 1}
                  </span>
                  <p className="text-foreground flex-1">{question}</p>
                  {canModifyConfig && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onRemoveQuestion(index)}
                      className="text-muted-foreground hover:text-destructive"
                      disabled={isSaving}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
            {questions.length === 0 && (
              <p className="text-muted-foreground text-center py-4">{t('view.setup.noQuestions')}</p>
            )}
          </div>

          {canModifyConfig && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex gap-2">
                <div className="flex-1">
                  <Label htmlFor="new-question" className="sr-only">{t('accessibility.addQuestion')}</Label>
                  <Input
                    id="new-question"
                    placeholder={t('view.setup.addQuestionPlaceholder')}
                    value={newQuestion}
                    onChange={(e) => onNewQuestionChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        onAddQuestion();
                      }
                    }}
                    disabled={isSaving}
                  />
                </div>
                <Button
                  onClick={onAddQuestion}
                  disabled={!newQuestion.trim() || isSaving}
                  className="bg-brand hover:bg-brand/90 text-brand-foreground"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Participants */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="text-card-foreground">{t('view.setup.participantsTitle')}</CardTitle>
              <p className="text-muted-foreground">
                {canModifyConfig
                  ? t('view.setup.participantsDescriptionEditable')
                  : t('view.setup.participantsDescriptionReadonly', { count: selectedPersonaIds.length })}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {personas.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">{t('view.setup.noPersonas')}</p>
            ) : (
              personas.map((persona) => {
                const isSelected = selectedPersonaIds.includes(persona.id);
                return (
                  <div
                    key={persona.id}
                    className={`flex items-center space-x-3 p-3 rounded-lg border transition-colors ${
                      isSelected
                        ? 'bg-brand-muted border-brand/40'
                        : 'bg-muted border-border'
                    }`}
                  >
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => onPersonaToggle(persona.id, checked === true)}
                      disabled={!canModifyConfig || isSaving}
                    />
                    <div className="flex-1">
                      <p className="text-card-foreground font-medium">
                        {persona.full_name || `Persona ${persona.id.slice(0, 8)}`}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {persona.age} {t('view.setup.yearsOld')} • {persona.occupation || t('view.setup.noOccupation')}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
