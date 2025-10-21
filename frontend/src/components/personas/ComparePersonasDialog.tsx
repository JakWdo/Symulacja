import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useComparePersonas } from '@/hooks/useComparePersonas';
import type { Persona, PersonaComparisonResponse, PersonaDetailsResponse } from '@/types';
import { Badge } from '@/components/ui/badge';

interface ComparePersonasDialogProps {
  persona: PersonaDetailsResponse;
  personas: Persona[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ComparePersonasDialog({ persona, personas, open, onOpenChange }: ComparePersonasDialogProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const mutation = useComparePersonas();
  const [result, setResult] = useState<PersonaComparisonResponse | null>(null);

  const available = personas.filter((p) => p.id !== persona.id);

  const handleCompare = () => {
    mutation.mutate(
      {
        personaId: persona.id,
        personaIds: selectedIds,
      },
      {
        onSuccess: (data) => setResult(data),
      },
    );
  };

  const close = () => {
    onOpenChange(false);
    setResult(null);
    mutation.reset();
  };

  const togglePersona = (id: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((pid) => pid !== id);
      }
      if (prev.length >= 2) {
        const [, ...rest] = prev;
        return [...rest, id];
      }
      return [...prev, id];
    });
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-w-5xl">
        <DialogHeader>
          <DialogTitle>Porównanie person</DialogTitle>
          <DialogDescription>
            Wybierz maksymalnie dwie inne persony, aby zobaczyć różnice w demografii, psychografii oraz KPI.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="space-y-2">
            <Label>Wybierz persony do porównania</Label>
            <div className="flex flex-wrap gap-2">
              {available.map((item) => (
                <Button
                  key={item.id}
                  variant={selectedIds.includes(item.id) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => togglePersona(item.id)}
                >
                  {item.full_name || item.persona_title || item.occupation || 'Persona'}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Wybrano: {selectedIds.length} / 2</p>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleCompare} disabled={mutation.isPending || selectedIds.length === 0}>
              {mutation.isPending ? 'Porównywanie...' : 'Porównaj'}
            </Button>
          </div>

          {result && (
            <ScrollArea className="max-h-[60vh] border rounded-lg">
              <div className="grid" style={{ gridTemplateColumns: `repeat(${result.personas.length}, minmax(220px, 1fr))` }}>
                {result.personas.map((item) => (
                  <div key={item.id} className="border-r last:border-r-0 border-border/60 p-4 space-y-3">
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">
                        {item.full_name || 'Persona'}
                      </h3>
                      <p className="text-xs text-muted-foreground">{item.age} lat • {item.location || 'Brak danych'}</p>
                      {item.segment_name && (
                        <Badge variant="outline" className="mt-1">{item.segment_name}</Badge>
                      )}
                    </div>

                    <section>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Demografia</p>
                      <ul className="space-y-1 text-xs text-foreground/90">
                        <li>Płeć: {item.gender}</li>
                        <li>Wykształcenie: {item.education_level || 'Brak'}</li>
                        <li>Dochód: {item.income_bracket || 'Brak'}</li>
                        <li>Zawód: {item.occupation || 'Brak'}</li>
                      </ul>
                    </section>

                    <section>
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Big Five</p>
                      <ul className="space-y-1 text-xs text-foreground/90">
                        {Object.entries(item.big_five).map(([trait, value]) => (
                          <li key={trait}>
                            {trait}: {value !== null && value !== undefined ? Math.round(Number(value) * 100) : '—'}%
                          </li>
                        ))}
                      </ul>
                    </section>

                    {item.kpi_snapshot && (
                      <section>
                        <p className="text-xs font-semibold text-muted-foreground mb-1">KPI</p>
                        <ul className="space-y-1 text-xs text-foreground/90">
                          <li>Segment size: {item.kpi_snapshot.segment_size?.toLocaleString?.() ?? '—'}</li>
                          <li>Conversion: {item.kpi_snapshot.conversion_rate ? `${(item.kpi_snapshot.conversion_rate * 100).toFixed(1)}%` : '—'}</li>
                          <li>Retention: {item.kpi_snapshot.retention_rate ? `${(item.kpi_snapshot.retention_rate * 100).toFixed(1)}%` : '—'}</li>
                          <li>LTV: {item.kpi_snapshot.ltv ? `${Math.round(item.kpi_snapshot.ltv).toLocaleString()} zł` : '—'}</li>
                        </ul>
                      </section>
                    )}
                  </div>
                ))}
              </div>

              <div className="border-t border-border/60 p-4 space-y-2 bg-muted/30">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Najważniejsze różnice</h4>
                {result.differences.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Persony są bardzo podobne.</p>
                ) : (
                  <ul className="space-y-1 text-xs text-foreground/90">
                    {result.differences.slice(0, 5).map((difference) => (
                      <li key={difference.field}>
                        <span className="font-medium">{difference.field}:</span>{' '}
                        {difference.values.map((value) => `${value.persona_id.slice(0, 8)} → ${Array.isArray(value.value) ? value.value.join(', ') : value.value ?? '—'}`).join(' | ')}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
