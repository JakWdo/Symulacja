/**
 * LLM Provider Settings Component
 *
 * Pozwala użytkownikowi wybrać preferowanego providera LLM (Gemini/OpenAI/Anthropic).
 *
 * Note: Ta implementacja jest frontend-only. Backend endpoint do zapisywania
 * preferred_llm_provider można dodać później.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';
import { Info, Sparkles } from 'lucide-react';

type LLMProvider = 'gemini' | 'openai' | 'anthropic';

interface ProviderInfo {
  name: string;
  description: string;
  models: string;
  pricing: string;
}

const PROVIDERS: Record<LLMProvider, ProviderInfo> = {
  gemini: {
    name: 'Google Gemini',
    description: 'Domyślny provider. Najlepszy stosunek jakości do ceny.',
    models: 'Gemini 2.5 Flash, Gemini 2.5 Pro',
    pricing: '~$0.10 / 1000 wywołań',
  },
  openai: {
    name: 'OpenAI',
    description: 'Wysoka jakość odpowiedzi, wyższe koszty.',
    models: 'GPT-4, GPT-3.5 Turbo',
    pricing: '~$0.50 / 1000 wywołań',
  },
  anthropic: {
    name: 'Anthropic Claude',
    description: 'Najlepszy dla złożonych zadań analitycznych.',
    models: 'Claude 3.5 Sonnet, Claude 3 Opus',
    pricing: '~$0.40 / 1000 wywołań',
  },
};

export function LLMProviderSettings() {
  // Domyślnie Gemini (można później pobierać z backendu)
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>('gemini');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);

    // TODO: Wysłać do backendu
    // await settingsApi.updateLLMProvider({ preferred_provider: selectedProvider });

    // Symulacja zapisu (usuń to gdy backend będzie gotowy)
    await new Promise(resolve => setTimeout(resolve, 500));

    toast({
      title: 'Ustawienia zapisane',
      description: `Provider LLM zmieniony na ${PROVIDERS[selectedProvider].name}`,
    });

    setIsSaving(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          Provider LLM
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-2">
          Wybierz preferowanego providera dla generacji AI. Provider jest używany dla nowych
          generacji (persony, grupy fokusowe, ankiety).
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex gap-3">
          <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Uwaga:</strong> Zmiana providera nie wpłynie na już wygenerowane dane.
            Nowy provider będzie używany tylko dla przyszłych generacji.
          </div>
        </div>

        <RadioGroup value={selectedProvider} onValueChange={(value) => setSelectedProvider(value as LLMProvider)}>
          <div className="space-y-4">
            {(Object.keys(PROVIDERS) as LLMProvider[]).map((provider) => {
              const info = PROVIDERS[provider];
              return (
                <div
                  key={provider}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedProvider === provider
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => setSelectedProvider(provider)}
                >
                  <div className="flex items-start gap-3">
                    <RadioGroupItem value={provider} id={provider} className="mt-1" />
                    <div className="flex-1">
                      <Label htmlFor={provider} className="text-base font-semibold cursor-pointer">
                        {info.name}
                        {provider === 'gemini' && (
                          <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                            Domyślny
                          </span>
                        )}
                      </Label>
                      <p className="text-sm text-muted-foreground mt-1">{info.description}</p>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="font-medium text-foreground">Modele:</span>
                          <span className="text-muted-foreground ml-1">{info.models}</span>
                        </div>
                        <div>
                          <span className="font-medium text-foreground">Koszt:</span>
                          <span className="text-muted-foreground ml-1">{info.pricing}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </RadioGroup>

        <div className="flex justify-end pt-4 border-t">
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Zapisywanie...' : 'Zapisz Ustawienia'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
