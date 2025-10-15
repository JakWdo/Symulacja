import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Users, AlertCircle, Check } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PersonaGenerationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerate: (config: PersonaGenerationConfig) => void;
}

export interface PersonaGenerationConfig {
  // Basic Setup
  personaCount: number;
  adversarialMode: boolean;
  demographicPreset: string;

  // Simplified - only general settings
  targetAudience: string; // e.g., "Young tech professionals", "Budget-conscious shoppers"
  focusArea: string; // e.g., "Technology", "Lifestyle", "Finance"

  // RAG is always enabled, demographics come from reports
}

const demographicPresets = [
  { id: 'gen-z', name: 'Gen Z (18-27)', description: 'Młodzi, cyfrowi tubylcy, świadomi wartości' },
  { id: 'millennials', name: 'Millennials (28-43)', description: 'Profesjonaliści znający się na technologii' },
  { id: 'gen-x', name: 'Gen X (44-59)', description: 'Ustabilizowana kariera, fokus na rodzinie' },
  { id: 'boomers', name: 'Baby Boomers (60+)', description: 'Tradycyjne wartości, stabilność' },
  { id: 'diverse', name: 'Zróżnicowana grupa', description: 'Mix wszystkich grup wiekowych i demografii' }
];

const focusAreas = [
  { id: 'technology', name: 'Technologia', description: 'Produkty tech, oprogramowanie, gadżety' },
  { id: 'lifestyle', name: 'Styl życia', description: 'Zdrowie, fitness, wellness, hobby' },
  { id: 'finance', name: 'Finanse', description: 'Bankowość, inwestycje, oszczędzanie' },
  { id: 'shopping', name: 'Zakupy', description: 'Retail, e-commerce, konsumpcja' },
  { id: 'entertainment', name: 'Rozrywka', description: 'Media, kultura, czas wolny' },
  { id: 'general', name: 'Ogólne', description: 'Szeroka perspektywa społeczna' }
];

export function PersonaGenerationWizard({ open, onOpenChange, onGenerate }: PersonaGenerationWizardProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [config, setConfig] = useState<PersonaGenerationConfig>({
    personaCount: 20,
    adversarialMode: false,
    demographicPreset: '',
    targetAudience: '',
    focusArea: '',
  });

  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const validateConfig = (): string[] => {
    const errors: string[] = [];

    if (config.personaCount < 2 || config.personaCount > 100) {
      errors.push('Liczba person musi być między 2 a 100');
    }

    if (!config.demographicPreset) {
      errors.push('Wybierz grupę demograficzną');
    }

    if (!config.focusArea) {
      errors.push('Wybierz obszar zainteresowań');
    }

    return errors;
  };

  const handleGenerate = async () => {
    const errors = validateConfig();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    setIsSubmitting(true);
    try {
      onGenerate(config);
      onOpenChange(false);
      // Reset wizard state
      setValidationErrors([]);
      setConfig({
        personaCount: 20,
        adversarialMode: false,
        demographicPreset: '',
        targetAudience: '',
        focusArea: '',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl w-full max-h-[90vh] bg-card dark:bg-[#11161d] border border-border text-foreground flex flex-col p-0 shadow-xl overflow-hidden">
        <div className="p-6 pb-4 bg-card dark:bg-transparent border-b border-border">
          <DialogHeader>
            <DialogTitle className="text-xl">Generator Person AI</DialogTitle>
            <DialogDescription>
              Stwórz zaawansowane persony AI z wykorzystaniem rzeczywistych danych demograficznych
            </DialogDescription>
          </DialogHeader>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <Alert className="mt-4 border-destructive/50 bg-destructive/10">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <AlertDescription className="text-destructive">
                <ul className="list-disc list-inside space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto px-6 pb-6 bg-card dark:bg-[#0d1218]">
          <div className="space-y-6 pt-4">
            {/* Number of Personas */}
            <div>
              <Label htmlFor="persona-count" className="text-base font-medium text-slate-900 dark:text-slate-300">
                Liczba Person
              </Label>
              <p className="text-sm text-muted-foreground mb-3 dark:text-slate-400">
                Ile person AI ma wygenerować? (2-100)
              </p>
              <Input
                id="persona-count"
                type="number"
                value={config.personaCount}
                onChange={(e) => setConfig(prev => ({ ...prev, personaCount: parseInt(e.target.value) || 20 }))}
                className="bg-input-background border-border"
                min="2"
                max="100"
              />
            </div>

            <Separator />

            {/* Demographic Preset */}
            <div>
              <Label className="text-base font-medium">Grupa Demograficzna</Label>
              <p className="text-sm text-muted-foreground mb-4">
                Wybierz grupę docelową - szczegóły demograficzne pochodzą z raportu RAG
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {demographicPresets.map((preset) => (
                  <Card
                    key={preset.id}
                    className={`cursor-pointer transition-all hover:shadow-elevated ${
                      config.demographicPreset === preset.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => {
                      setConfig(prev => ({ ...prev, demographicPreset: preset.id }));
                    }}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{preset.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{preset.description}</p>
                        </div>
                        {config.demographicPreset === preset.id && (
                          <Check className="w-4 h-4 text-primary mt-0.5" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <Separator />

            {/* Focus Area */}
            <div>
              <Label className="text-base font-medium">Obszar Zainteresowań</Label>
              <p className="text-sm text-muted-foreground mb-4">
                Wybierz główny obszar badania - persony będą dostosowane do tego kontekstu
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {focusAreas.map((area) => (
                  <Card
                    key={area.id}
                    className={`cursor-pointer transition-all hover:shadow-elevated ${
                      config.focusArea === area.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => {
                      setConfig(prev => ({ ...prev, focusArea: area.id }));
                    }}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{area.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{area.description}</p>
                        </div>
                        {config.focusArea === area.id && (
                          <Check className="w-4 h-4 text-primary mt-0.5" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <Separator />

            {/* Additional Description (optional) */}
            <div>
              <Label htmlFor="target-audience" className="text-base font-medium">
                Dodatkowy Opis (opcjonalnie)
              </Label>
              <p className="text-sm text-muted-foreground mb-3">
                Opisz dokładniej grupę docelową lub specyficzne wymagania
              </p>
              <div className="relative space-y-2">
                <Textarea
                  id="target-audience"
                  value={config.targetAudience}
                  onChange={(e) => {
                    const value = e.target.value.slice(0, 500);
                    setConfig(prev => ({ ...prev, targetAudience: value }));
                  }}
                  maxLength={500}
                  className="bg-input-background border-border"
                  placeholder="np. 'Osoby zainteresowane zrównoważonym rozwojem i ekologicznymi produktami'"
                  rows={3}
                />
                <div
                  className={`text-xs ${
                    config.targetAudience.length > 400
                      ? 'text-red-500'
                      : config.targetAudience.length > 300
                      ? 'text-yellow-500'
                      : 'text-muted-foreground'
                  }`}
                >
                  {config.targetAudience.length}/500 znaków
                  {config.targetAudience.length > 300 && ' - Krótszy opis = lepsze wyniki'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col sm:flex-row sm:justify-between gap-3 p-6 pt-4 border-t border-border bg-card dark:bg-[#11161d]">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
            className="border-border w-full sm:w-auto"
          >
            Anuluj
          </Button>

          <Button
            onClick={handleGenerate}
            disabled={isSubmitting}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white w-full sm:w-auto"
          >
            <Users className="w-4 h-4 mr-2" />
            {isSubmitting ? 'Generowanie...' : `Generuj ${config.personaCount} Person`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
