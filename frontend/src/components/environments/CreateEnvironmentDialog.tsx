import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';
import { createEnvironment } from '@/api/environments';
import { getMyTeams } from '@/api/teams';
import { toast } from '@/hooks/use-toast';
import { useQuery } from '@tanstack/react-query';

interface CreateEnvironmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateEnvironmentDialog({ open, onOpenChange }: CreateEnvironmentDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const queryClient = useQueryClient();

  // Pobierz teams użytkownika
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: getMyTeams,
  });

  const currentTeam = teamsData?.teams?.[0]; // Użyj pierwszego teamu

  const createMutation = useMutation({
    mutationFn: createEnvironment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      toast({
        title: 'Środowisko utworzone',
        description: `Środowisko "${name}" zostało pomyślnie utworzone.`,
      });
      setName('');
      setDescription('');
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się utworzyć środowiska',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && currentTeam) {
      createMutation.mutate({
        team_id: currentTeam.id,
        name: name.trim(),
        description: description.trim() || undefined,
      });
    }
  };

  if (!currentTeam) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Brak zespołu</DialogTitle>
            <DialogDescription>
              Musisz należeć do zespołu, aby utworzyć środowisko.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => onOpenChange(false)}>Zamknij</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Utwórz Nowe Środowisko</DialogTitle>
          <DialogDescription>
            Stwórz środowisko do organizowania i filtrowania zasobów dla zespołu {currentTeam.name}.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="env-name">
              Nazwa Środowiska <span className="text-destructive">*</span>
            </Label>
            <Input
              id="env-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="np. Produkcja, Rozwój, Test"
              required
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="env-description">Opis (opcjonalnie)</Label>
            <Textarea
              id="env-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Krótki opis środowiska i jego przeznaczenia..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createMutation.isPending}
            >
              Anuluj
            </Button>
            <Button type="submit" disabled={!name.trim() || createMutation.isPending}>
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Utwórz Środowisko
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
