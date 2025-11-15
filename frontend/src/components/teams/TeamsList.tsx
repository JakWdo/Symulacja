import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Plus,
  Search,
  Users,
  Folder,
  Settings,
  Crown,
  Eye,
  UserPlus,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Logo } from '@/components/ui/logo';
import { CreateTeamDialog } from './CreateTeamDialog';
import * as teamsApi from '@/api/teams';
import type { Team } from '@/api/teams';
import { useAppStore } from '@/store/appStore';

interface TeamsListProps {
  onSelectTeam?: (team: Team) => void;
}

export function TeamsList({ onSelectTeam }: TeamsListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const queryClient = useQueryClient();
  const currentTeamId = useAppStore((state) => state.currentTeamId);
  const setCurrentTeamId = useAppStore((state) => state.setCurrentTeamId);

  // Fetch teams
  const { data: teamsData, isLoading } = useQuery({
    queryKey: ['teams'],
    queryFn: () => teamsApi.getMyTeams(),
  });

  const teams = teamsData?.teams || [];

  const filteredTeams = teams.filter((team: Team) =>
    team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (team.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
  );

  const getRoleIcon = (memberCount?: number) => {
    if (!memberCount) return <Users className="w-4 h-4" />;
    if (memberCount === 1) return <Crown className="w-4 h-4" />;
    if (memberCount <= 3) return <Users className="w-4 h-4" />;
    return <UserPlus className="w-4 h-4" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Logo className="w-8 h-8" spinning />
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
        {/* Header */}
        <PageHeader
          title="Zespoły"
          subtitle="Zarządzaj zespołami i współpracownikami"
          actions={
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              Nowy Zespół
            </Button>
          }
        />

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            type="text"
            placeholder="Szukaj zespołów..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Teams Grid */}
        {filteredTeams.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Users className="w-12 h-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {searchTerm ? 'Brak wyników' : 'Brak zespołów'}
              </h3>
              <p className="text-muted-foreground text-center mb-4">
                {searchTerm
                  ? 'Spróbuj innego wyszukiwania'
                  : 'Utwórz swój pierwszy zespół, aby rozpocząć współpracę'}
              </p>
              {!searchTerm && (
                <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                  <Plus className="w-4 h-4" />
                  Utwórz Zespół
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTeams.map((team) => (
              <Card
                key={team.id}
                className={`cursor-pointer hover:border-primary transition-colors ${
                  team.id === currentTeamId ? 'border-primary shadow-md' : ''
                }`}
                onClick={() => {
                  setCurrentTeamId(team.id);
                  onSelectTeam?.(team);
                }}
              >
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-lg font-semibold">
                      {team.name}
                    </CardTitle>
                    {team.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {team.description}
                      </p>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        {getRoleIcon(team.member_count)}
                        <span>{team.member_count || 0} członków</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Folder className="w-4 h-4" />
                        <span>{team.project_count || 0} projektów</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      {team.is_active ? 'Aktywny' : 'Nieaktywny'}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setCurrentTeamId(team.id);
                        onSelectTeam?.(team);
                      }}
                      className="gap-2"
                    >
                      <Settings className="w-4 h-4" />
                      Zarządzaj
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Team Dialog */}
      <CreateTeamDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      />
    </div>
  );
}
