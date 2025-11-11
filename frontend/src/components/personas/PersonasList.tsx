/**
 * PersonasList - Karuzela/lista person z nawigacją i szczegółami
 * Wyodrębnione z Personas.tsx (Zadanie 36)
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import {
  ChevronLeft,
  ChevronRight,
  Keyboard,
  MoreVertical,
  Eye,
  Trash2,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { formatAge, extractFirstName, type DisplayPersona } from '@/components/personas/helpers/transformers';

export interface PersonasListProps {
  filteredPersonas: DisplayPersona[];
  currentPersonaIndex: number;
  onIndexChange: (index: number) => void;
  onViewDetails: (personaId: string) => void;
  onDelete: (persona: DisplayPersona) => void;
}

export function PersonasList({
  filteredPersonas,
  currentPersonaIndex,
  onIndexChange,
  onViewDetails,
  onDelete,
}: PersonasListProps) {
  const { t } = useTranslation('personas');

  const currentPersona = filteredPersonas[currentPersonaIndex] ?? null;
  const currentPersonaName = currentPersona ? extractFirstName(currentPersona.name) : '';
  const currentPersonaAgeLabel = currentPersona ? formatAge(currentPersona.age) : '';

  return (
    <div className="lg:col-span-8 space-y-4">
      <Card
        className="bg-card border border-border overflow-y-auto focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2"
        style={{ maxHeight: '600px' }}
        tabIndex={0}
        role="region"
        aria-label="Karuzela person"
        aria-live="polite"
        aria-atomic="true"
      >
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onIndexChange(Math.max(0, currentPersonaIndex - 1))}
                disabled={currentPersonaIndex === 0}
                className="h-8 w-8 p-0"
                aria-label="Poprzednia persona"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                {currentPersonaIndex + 1} {t('page.carousel.of')} {filteredPersonas.length}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onIndexChange(Math.min(filteredPersonas.length - 1, currentPersonaIndex + 1))}
                disabled={currentPersonaIndex === filteredPersonas.length - 1}
                className="h-8 w-8 p-0"
                aria-label="Następna persona"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>

              {/* Keyboard shortcuts tooltip */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <Keyboard className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">
                    <p><kbd className="px-1 py-0.5 bg-muted rounded">←</kbd> <kbd className="px-1 py-0.5 bg-muted rounded">→</kbd> Nawigacja</p>
                    <p><kbd className="px-1 py-0.5 bg-muted rounded">Home</kbd> Pierwsza | <kbd className="px-1 py-0.5 bg-muted rounded">End</kbd> Ostatnia</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <div className="flex gap-2">
              {filteredPersonas.map((_, index) => (
                <button
                  key={index}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === currentPersonaIndex ? 'bg-primary' : 'bg-muted'
                  }`}
                  onClick={() => onIndexChange(index)}
                  aria-label={`Przejdź do persony ${index + 1}`}
                />
              ))}
            </div>
          </div>

          {/* Aktualnie wybrana persona */}
          {currentPersona && (
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-xl text-card-foreground mb-1">
                    {currentPersonaName ? `${currentPersonaName}, ${currentPersonaAgeLabel}` : `${currentPersona.name}`}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {currentPersona.occupation}
                  </p>
                  <p className="text-muted-foreground">
                    {currentPersona.demographics.location}
                  </p>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem onClick={() => onViewDetails(currentPersona.id)}>
                      <Eye className="w-4 h-4 mr-2" />
                      {t('page.carousel.viewDetails')}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(currentPersona);
                      }}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      {t('page.carousel.deletePersona')}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Background */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-card-foreground">{t('page.carousel.context')}</h4>
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                  {currentPersona.background}
                </p>
              </div>

              {/* Demographics Grid - responsive */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="space-y-0.5">
                  <p className="text-xs text-muted-foreground">{t('page.carousel.demographics.gender')}</p>
                  <p className="text-sm text-card-foreground">{currentPersona.demographics.gender}</p>
                </div>
                <div className="space-y-0.5">
                  <p className="text-xs text-muted-foreground">{t('page.carousel.demographics.education')}</p>
                  <p className="text-sm text-card-foreground">{currentPersona.demographics.education}</p>
                </div>
                <div className="space-y-0.5">
                  <p className="text-xs text-muted-foreground">{t('page.carousel.demographics.income')}</p>
                  <p className="text-sm text-card-foreground">{currentPersona.demographics.income}</p>
                </div>
                <div className="space-y-0.5">
                  <p className="text-xs text-muted-foreground">{t('page.carousel.demographics.lifestyle')}</p>
                  <p className="text-sm text-card-foreground line-clamp-1">{currentPersona.psychographics.lifestyle}</p>
                </div>
              </div>

              {/* Interests */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-card-foreground">{t('page.carousel.interestsAndValues')}</h4>
                <div className="space-y-1.5">
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">{t('page.carousel.interests')}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {currentPersona.interests.slice(0, 5).map((interest, index) => (
                        <Badge key={index} variant="secondary" className="bg-primary/10 text-primary border-primary/20 text-xs py-0">
                          {interest}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">{t('page.carousel.values')}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {currentPersona.psychographics.values.slice(0, 5).map((value, index) => (
                        <Badge key={index} variant="outline" className="border-secondary text-secondary text-xs py-0">
                          {value}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Creation Date */}
              <div className="pt-2">
                <p className="text-xs text-muted-foreground text-right">
                  {t('page.carousel.createdOn')} {new Date(filteredPersonas[currentPersonaIndex].createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
