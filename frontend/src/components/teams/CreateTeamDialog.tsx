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
import * as teamsApi from '@/api/teams';
import { toast } from '@/components/ui/use-toast';

interface CreateTeamDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateTeamDialog({ open, onOpenChange }: CreateTeamDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: teamsApi.createTeam,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Zespół utworzony',
        description: `Zespół "${name}" został pomyślnie utworzony.`,
      });
      setName('');
      setDescription('');
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się utworzyć zespołu',
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      createMutation.mutate({
        name: name.trim(),
        description: description.trim() || undefined,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Utwórz Nowy Zespół</DialogTitle>
          <DialogDescription>
            Stwórz zespół, aby współpracować z innymi nad projektami badawczymi.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="team-name">
              Nazwa Zespołu <span className="text-destructive">*</span>
            </Label>
            <Input
              id="team-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="np. Marketing Team"
              required
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="team-description">Opis (opcjonalnie)</Label>
            <Textarea
              id="team-description"
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
              disabled={createMutation.isPending}
            >
              Anuluj
            </Button>
            <Button type="submit" disabled={!name.trim() || createMutation.isPending}>
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Utwórz Zespół
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
