import { useState } from 'react';
import { useMutation, useQueryClient } from '@tantml:query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { UserPlus, Trash2, Crown, Users, Eye, Loader2 } from 'lucide-react';
import * as teamsApi from '@/api/teams';
import type { Team, TeamMember, TeamRole } from '@/api/teams';
import { toast } from '@/components/ui/use-toast';
import { formatDate } from '@/lib/utils';

interface ManageMembersDialogProps {
  team: Team;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ManageMembersDialog({
  team,
  open,
  onOpenChange,
}: ManageMembersDialogProps) {
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [newMemberRole, setNewMemberRole] = useState<TeamRole>('member');
  const queryClient = useQueryClient();

  // Add member mutation
  const addMemberMutation = useMutation({
    mutationFn: (data: { email: string; role_in_team: TeamRole }) =>
      teamsApi.addTeamMember(team.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', team.id] });
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Członek dodany',
        description: `Użytkownik ${newMemberEmail} został dodany do zespołu.`,
      });
      setNewMemberEmail('');
      setNewMemberRole('member');
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się dodać członka',
        variant: 'destructive',
      });
    },
  });

  // Update role mutation
  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: TeamRole }) =>
      teamsApi.updateTeamMemberRole(team.id, userId, { role_in_team: role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', team.id] });
      toast({
        title: 'Rola zaktualizowana',
        description: 'Rola członka została pomyślnie zaktualizowana.',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się zaktualizować roli',
        variant: 'destructive',
      });
    },
  });

  // Remove member mutation
  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => teamsApi.removeTeamMember(team.id, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', team.id] });
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Członek usunięty',
        description: 'Członek został usunięty z zespołu.',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się usunąć członka',
        variant: 'destructive',
      });
    },
  });

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMemberEmail.trim()) {
      addMemberMutation.mutate({
        email: newMemberEmail.trim(),
        role_in_team: newMemberRole,
      });
    }
  };

  const handleUpdateRole = (userId: string, newRole: TeamRole) => {
    updateRoleMutation.mutate({ userId, role: newRole });
  };

  const handleRemoveMember = (member: TeamMember) => {
    if (
      confirm(
        `Czy na pewno chcesz usunąć ${member.full_name} z zespołu? ${
          member.role_in_team === 'owner'
            ? 'Uwaga: Usunięcie ostatniego właściciela może uniemożliwić zarządzanie zespołem.'
            : ''
        }`
      )
    ) {
      removeMemberMutation.mutate(member.user_id);
    }
  };

  const getRoleIcon = (role: TeamRole) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4" />;
      case 'member':
        return <Users className="w-4 h-4" />;
      case 'viewer':
        return <Eye className="w-4 h-4" />;
    }
  };

  const getRoleLabel = (role: TeamRole) => {
    switch (role) {
      case 'owner':
        return 'Właściciel';
      case 'member':
        return 'Członek';
      case 'viewer':
        return 'Przeglądający';
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Zarządzaj Członkami</DialogTitle>
          <DialogDescription>
            Dodawaj, usuwaj i zarządzaj rolami członków zespołu "{team.name}".
          </DialogDescription>
        </DialogHeader>

        {/* Add Member Form */}
        <form onSubmit={handleAddMember} className="space-y-4 border-b pb-4">
          <h3 className="font-medium flex items-center gap-2">
            <UserPlus className="w-4 h-4" />
            Dodaj Nowego Członka
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-2">
              <Label htmlFor="member-email">Email</Label>
              <Input
                id="member-email"
                type="email"
                value={newMemberEmail}
                onChange={(e) => setNewMemberEmail(e.target.value)}
                placeholder="member@example.com"
                disabled={addMemberMutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="member-role">Rola</Label>
              <Select
                value={newMemberRole}
                onValueChange={(value) => setNewMemberRole(value as TeamRole)}
                disabled={addMemberMutation.isPending}
              >
                <SelectTrigger id="member-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="owner">
                    <div className="flex items-center gap-2">
                      <Crown className="w-4 h-4" />
                      Właściciel
                    </div>
                  </SelectItem>
                  <SelectItem value="member">
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      Członek
                    </div>
                  </SelectItem>
                  <SelectItem value="viewer">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      Przeglądający
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            type="submit"
            disabled={!newMemberEmail.trim() || addMemberMutation.isPending}
            className="w-full"
          >
            {addMemberMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Dodaj Członka
          </Button>
        </form>

        {/* Members List */}
        <div className="space-y-2">
          <h3 className="font-medium">Obecni Członkowie ({team.members?.length || 0})</h3>

          {team.members && team.members.length > 0 ? (
            <div className="space-y-2">
              {team.members.map((member: TeamMember) => (
                <div
                  key={member.user_id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>{getInitials(member.full_name)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium">{member.full_name}</div>
                      <div className="text-sm text-muted-foreground">{member.email}</div>
                      <div className="text-xs text-muted-foreground">
                        Dołączył: {formatDate(member.joined_at)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Select
                      value={member.role_in_team}
                      onValueChange={(value) =>
                        handleUpdateRole(member.user_id, value as TeamRole)
                      }
                      disabled={updateRoleMutation.isPending}
                    >
                      <SelectTrigger className="w-[150px]">
                        <div className="flex items-center gap-2">
                          {getRoleIcon(member.role_in_team)}
                          <SelectValue />
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="owner">
                          <div className="flex items-center gap-2">
                            <Crown className="w-4 h-4" />
                            Właściciel
                          </div>
                        </SelectItem>
                        <SelectItem value="member">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            Członek
                          </div>
                        </SelectItem>
                        <SelectItem value="viewer">
                          <div className="flex items-center gap-2">
                            <Eye className="w-4 h-4" />
                            Przeglądający
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveMember(member)}
                      disabled={removeMemberMutation.isPending}
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>Brak członków w zespole</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
