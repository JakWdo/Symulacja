import { memo, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { RefreshCw, User, Users, Sparkles } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { personasApi } from '@/lib/api';
import { toast } from 'sonner';

interface RegenerateButtonProps {
  personaId: string;
  disabled?: boolean;
}

/**
 * RegenerateButton - dropdown menu do regeneracji narratywów
 *
 * Opcje:
 * - Osoba (person_profile + person_motivations)
 * - Segment (segment_hero + segment_significance + evidence_context)
 * - Wszystko (all narratives)
 *
 * Rate limiting: 10 req/h (429 error handling)
 * Loading state: Spinner + disabled button
 * Success: Toast notification + React Query invalidation
 */
export const RegenerateButton = memo<RegenerateButtonProps>(
  ({ personaId, disabled = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const queryClient = useQueryClient();

    const regenerateMutation = useMutation({
      mutationFn: async (scope: 'person' | 'segment' | 'all') => {
        return await personasApi.regenerateNarratives(personaId, scope);
      },
      onSuccess: (_data, scope) => {
        // Invalidate cache to trigger refetch
        queryClient.invalidateQueries({
          queryKey: ['personas', personaId, 'details'],
        });

        // Show success toast
        const scopeLabel =
          scope === 'person'
            ? 'opisy osoby'
            : scope === 'segment'
            ? 'opisy segmentu'
            : 'wszystkie opisy';
        toast.success(`Zaktualizowano ${scopeLabel}`);
      },
      onError: (error: any) => {
        // Handle rate limiting
        if (error.response?.status === 429) {
          toast.error('Przekroczono limit regeneracji (10 na godzinę)', {
            description: 'Spróbuj ponownie później.',
          });
        } else {
          toast.error('Nie udało się zregenerować opisów', {
            description: error.message || 'Wystąpił nieoczekiwany błąd.',
          });
        }
      },
    });

    const handleRegenerate = async (scope: 'person' | 'segment' | 'all') => {
      setIsOpen(false);
      await regenerateMutation.mutateAsync(scope);
    };

    const isRegenerating = regenerateMutation.isPending;

    return (
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || isRegenerating}
            className="gap-2"
            aria-label="Regeneruj opisy"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`}
            />
            Regeneruj
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuItem
            onClick={() => handleRegenerate('person')}
            disabled={isRegenerating}
            className="cursor-pointer"
          >
            <User className="w-4 h-4 mr-2" />
            <div className="flex flex-col">
              <span className="font-medium">Osoba</span>
              <span className="text-xs text-muted-foreground">
                Profil i motywacje
              </span>
            </div>
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => handleRegenerate('segment')}
            disabled={isRegenerating}
            className="cursor-pointer"
          >
            <Users className="w-4 h-4 mr-2" />
            <div className="flex flex-col">
              <span className="font-medium">Segment</span>
              <span className="text-xs text-muted-foreground">
                Wprowadzenie i znaczenie
              </span>
            </div>
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          <DropdownMenuItem
            onClick={() => handleRegenerate('all')}
            disabled={isRegenerating}
            className="cursor-pointer"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            <div className="flex flex-col">
              <span className="font-medium">Wszystko</span>
              <span className="text-xs text-muted-foreground">
                Pełna regeneracja
              </span>
            </div>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }
);

RegenerateButton.displayName = 'RegenerateButton';
