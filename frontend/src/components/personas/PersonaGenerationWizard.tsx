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
import { useTranslation } from 'react-i18next';

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

// Demographic presets and focus areas will be translated dynamically

export function PersonaGenerationWizard({ open, onOpenChange, onGenerate }: PersonaGenerationWizardProps) {
  const { t } = useTranslation('personas');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [config, setConfig] = useState<PersonaGenerationConfig>({
    personaCount: 20,
    adversarialMode: false,
    demographicPreset: '',
    targetAudience: '',
    focusArea: '',
  });

  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Dynamically build demographic presets from translations
  const demographicPresets = [
    { id: 'gen-z', name: t('wizard.demographic.presets.genZ.name'), description: t('wizard.demographic.presets.genZ.description') },
    { id: 'millennials', name: t('wizard.demographic.presets.millennials.name'), description: t('wizard.demographic.presets.millennials.description') },
    { id: 'gen-x', name: t('wizard.demographic.presets.genX.name'), description: t('wizard.demographic.presets.genX.description') },
    { id: 'boomers', name: t('wizard.demographic.presets.boomers.name'), description: t('wizard.demographic.presets.boomers.description') },
    { id: 'diverse', name: t('wizard.demographic.presets.diverse.name'), description: t('wizard.demographic.presets.diverse.description') }
  ];

  // Dynamically build focus areas from translations
  const focusAreas = [
    { id: 'technology', name: t('wizard.focusArea.areas.technology.name'), description: t('wizard.focusArea.areas.technology.description') },
    { id: 'lifestyle', name: t('wizard.focusArea.areas.lifestyle.name'), description: t('wizard.focusArea.areas.lifestyle.description') },
    { id: 'finance', name: t('wizard.focusArea.areas.finance.name'), description: t('wizard.focusArea.areas.finance.description') },
    { id: 'shopping', name: t('wizard.focusArea.areas.shopping.name'), description: t('wizard.focusArea.areas.shopping.description') },
    { id: 'entertainment', name: t('wizard.focusArea.areas.entertainment.name'), description: t('wizard.focusArea.areas.entertainment.description') },
    { id: 'general', name: t('wizard.focusArea.areas.general.name'), description: t('wizard.focusArea.areas.general.description') }
  ];

  const validateConfig = (): string[] => {
    const errors: string[] = [];

    if (config.personaCount < 2 || config.personaCount > 100) {
      errors.push(t('wizard.validation.countRange'));
    }

    if (!config.demographicPreset) {
      errors.push(t('wizard.validation.selectDemographic'));
    }

    if (!config.focusArea) {
      errors.push(t('wizard.validation.selectFocus'));
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
      <DialogContent className="max-w-3xl w-full max-h-[90vh] bg-card border border-border text-foreground flex flex-col p-0 shadow-xl overflow-hidden">
        <div className="p-6 pb-4 bg-card dark:bg-transparent border-b border-border">
          <DialogHeader>
            <DialogTitle className="text-xl">{t('wizard.title')}</DialogTitle>
            <DialogDescription>
              {t('wizard.subtitle')}
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
        <div className="flex-1 overflow-y-auto px-6 pb-6 bg-card">
          <div className="space-y-6 pt-4">
            {/* Number of Personas */}
            <div>
              <Label htmlFor="persona-count" className="text-base font-medium text-slate-900 dark:text-slate-300">
                {t('wizard.count.label')}
              </Label>
              <p className="text-sm text-muted-foreground mb-3 dark:text-slate-400">
                {t('wizard.count.description')}
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
              <Label className="text-base font-medium">{t('wizard.demographic.label')}</Label>
              <p className="text-sm text-muted-foreground mb-4">
                {t('wizard.demographic.description')}
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
              <Label className="text-base font-medium">{t('wizard.focusArea.label')}</Label>
              <p className="text-sm text-muted-foreground mb-4">
                {t('wizard.focusArea.description')}
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
                {t('wizard.additionalDescription.label')}
              </Label>
              <p className="text-sm text-muted-foreground mb-3">
                {t('wizard.additionalDescription.description')}
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
                  placeholder={t('wizard.additionalDescription.placeholder')}
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
                  {config.targetAudience.length}/500 {t('wizard.additionalDescription.charLimit')}
                  {config.targetAudience.length > 300 && ` - ${t('wizard.additionalDescription.charWarning')}`}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col sm:flex-row sm:justify-between gap-3 p-6 pt-4 border-t border-border bg-card">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
            className="border-border w-full sm:w-auto"
          >
            {t('wizard.cancelButton')}
          </Button>

          <Button
            onClick={handleGenerate}
            disabled={isSubmitting}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white w-full sm:w-auto"
          >
            <Users className="w-4 h-4 mr-2" />
            {isSubmitting ? t('wizard.generatingButton') : t('wizard.generateButton', { count: config.personaCount })}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
