import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useGenerateMessaging } from '@/hooks/useGenerateMessaging';
import type { PersonaMessagingResponse } from '@/types';
import { Badge } from '@/components/ui/badge';

interface MessagingGeneratorDialogProps {
  personaId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const TONES = [
  { value: 'friendly', label: 'Przyjazny' },
  { value: 'professional', label: 'Profesjonalny' },
  { value: 'urgent', label: 'Pilny' },
  { value: 'empathetic', label: 'Empatyczny' },
];

const FORMATS = [
  { value: 'email', label: 'E-mail' },
  { value: 'ad', label: 'Reklama display' },
  { value: 'landing_page', label: 'Landing Page' },
  { value: 'social_post', label: 'Post w social media' },
];

export function MessagingGeneratorDialog({ personaId, open, onOpenChange }: MessagingGeneratorDialogProps) {
  const [tone, setTone] = useState<string>('friendly');
  const [format, setFormat] = useState<string>('email');
  const [context, setContext] = useState<string>('');
  const [result, setResult] = useState<PersonaMessagingResponse | null>(null);
  const mutation = useGenerateMessaging();

  const handleGenerate = () => {
    mutation.mutate(
      {
        personaId,
        tone: tone as any,
        type: format as any,
        context: context || undefined,
      },
      {
        onSuccess: (data) => {
          setResult(data);
        },
      },
    );
  };

  const close = () => {
    onOpenChange(false);
    setResult(null);
    mutation.reset();
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Generuj komunikację</DialogTitle>
          <DialogDescription>
            Wygeneruj warianty messagingu dla tej persony na podstawie aktualnych danych i insightów.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="tone">Ton komunikacji</Label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger id="tone">
                  <SelectValue placeholder="Wybierz ton" />
                </SelectTrigger>
                <SelectContent>
                  {TONES.map((item) => (
                    <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="format">Format</Label>
              <Select value={format} onValueChange={setFormat}>
                <SelectTrigger id="format">
                  <SelectValue placeholder="Wybierz format" />
                </SelectTrigger>
                <SelectContent>
                  {FORMATS.map((item) => (
                    <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="context">Dodatkowy kontekst (opcjonalnie)</Label>
            <Textarea
              id="context"
              value={context}
              onChange={(event) => setContext(event.target.value)}
              placeholder="Podaj cel kampanii, CTA, kluczowe produkty..."
            />
          </div>

          <div className="flex justify-between items-center">
            <p className="text-xs text-muted-foreground">
              Generowanie trwa zwykle kilka sekund. Każda iteracja wykorzystuje Gemini Flash.
            </p>
            <Button onClick={handleGenerate} disabled={mutation.isPending}>
              {mutation.isPending ? 'Generowanie...' : 'Generuj warianty'}
            </Button>
          </div>

          {result && result.variants.length > 0 && (
            <div className="mt-4">
              <Tabs defaultValue={`variant-${result.variants[0].variant_id}`}>
                <TabsList>
                  {result.variants.map((variant) => (
                    <TabsTrigger key={variant.variant_id} value={`variant-${variant.variant_id}`}>
                      Wariant {variant.variant_id}
                    </TabsTrigger>
                  ))}
                </TabsList>

                {result.variants.map((variant) => (
                  <TabsContent key={variant.variant_id} value={`variant-${variant.variant_id}`} className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-foreground">{variant.headline}</p>
                      {variant.subheadline && (
                        <p className="text-sm text-muted-foreground">{variant.subheadline}</p>
                      )}
                    </div>
                    <div className="text-sm leading-relaxed whitespace-pre-line bg-muted/40 border border-border/60 rounded-lg p-4">
                      {variant.body}
                    </div>
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary">CTA: {variant.cta}</Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigator.clipboard.writeText(`${variant.headline}\n\n${variant.body}\n\nCTA: ${variant.cta}`)}
                      >
                        Kopiuj do schowka
                      </Button>
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
