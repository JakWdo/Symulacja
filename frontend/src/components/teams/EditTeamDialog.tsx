import { useState, useEffect } from 'react';
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
import * as teamsApi from '@/api/teams';
import type { Team } from '@/api/teams';
import { toast } from '@/components/ui/use-toast';

interface EditTeamDialogProps {
  team: Team;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditTeamDialog({ team, open, onOpenChange }: EditTeamDialogProps) {
  const [name, setName] = useState(team.name);
  const [description, setDescription] = useState(team.description || '');
  const queryClient = useQueryClient();

  // Reset form when team changes
  useEffect(() => {
    setName(team.name);
    setDescription(team.description || '');
  }, [team]);

  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; description?: string }) =>
      teamsApi.updateTeam(team.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', team.id] });
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Zespół zaktualizowany',
        description: `Dane zespołu "${name}" zostały pomyślnie zaktualizowane.`,
      });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się zaktualizować zespołu',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      updateMutation.mutate({
        name: name.trim(),
        description: description.trim() || undefined,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edytuj Zespół</DialogTitle>
          <DialogDescription>
            Zaktualizuj informacje o zespole "{team.name}".
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-team-name">
              Nazwa Zespołu <span className="text-destructive">*</span>
            </Label>
            <Input
              id="edit-team-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="np. Marketing Team"
              required
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-team-description">Opis (opcjonalnie)</Label>
            <Textarea
              id="edit-team-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Krótki opis zespołu i jego celów..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateMutation.isPending}
            >
              Anuluj
            </Button>
            <Button type="submit" disabled={!name.trim() || updateMutation.isPending}>
              {updateMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Zapisz Zmiany
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
