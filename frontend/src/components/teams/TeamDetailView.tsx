import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  ArrowLeft,
  Users,
  Folder,
  UserPlus,
  Crown,
  Eye,
  Edit,
  Trash2,
  MoreVertical,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { PageHeader } from '@/components/layout/PageHeader';
import { Logo } from '@/components/ui/logo';
import { ManageMembersDialog } from './ManageMembersDialog';
import { EditTeamDialog } from './EditTeamDialog';
import * as teamsApi from '@/api/teams';
import type { TeamMember, TeamRole } from '@/api/teams';
import { toast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/utils';
import { listEnvironments, type Environment } from '@/api/environments';
import { projectsApi } from '@/lib/api/projects';
import type { Project } from '@/types';
import { useAppStore } from '@/store/appStore';

interface TeamDetailViewProps {
  teamId: string;
  onBack: () => void;
}

export function TeamDetailView({ teamId, onBack }: TeamDetailViewProps) {
  const [showMembersDialog, setShowMembersDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const queryClient = useQueryClient();
  const setCurrentTeamId = useAppStore((state) => state.setCurrentTeamId);
  const setCurrentEnvironmentId = useAppStore((state) => state.setCurrentEnvironmentId);
  const setSelectedProject = useAppStore((state) => state.setSelectedProject);

  // Fetch team details
  const { data: team, isLoading } = useQuery({
    queryKey: ['teams', teamId],
    queryFn: () => teamsApi.getTeam(teamId),
  });

  // Powiąż globalny kontekst z aktualnym zespołem
  if (team) {
    setCurrentTeamId(team.id);
  }

  // Środowiska zespołu
  const { data: environments = [], isLoading: environmentsLoading } = useQuery({
    queryKey: ['environments', teamId],
    queryFn: () => listEnvironments(teamId),
    enabled: !!teamId,
  });

  // Projekty zespołu
  const { data: projects = [], isLoading: projectsLoading } = useQuery<Project[]>({
    queryKey: ['projects', { teamId }],
    queryFn: () =>
      projectsApi.getAll({
        teamId,
      }),
    enabled: !!teamId,
  });

  // Delete team mutation
  const deleteMutation = useMutation({
    mutationFn: () => teamsApi.deleteTeam(teamId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      toast({
        title: 'Zespół usunięty',
        description: `Zespół "${team?.name}" został usunięty.`,
      });
      onBack();
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.response?.data?.detail || 'Nie udało się usunąć zespołu',
        variant: 'destructive',
      });
    },
  });

  const handleDeleteTeam = () => {
    if (confirm(`Czy na pewno chcesz usunąć zespół "${team?.name}"? Ta akcja jest nieodwracalna.`)) {
      deleteMutation.mutate();
    }
  };

  const getRoleIcon = (role: TeamRole) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'member':
        return <Users className="w-4 h-4 text-blue-500" />;
      case 'viewer':
        return <Eye className="w-4 h-4 text-gray-500" />;
    }
  };

  const getRoleBadgeVariant = (role: TeamRole) => {
    switch (role) {
      case 'owner':
        return 'default';
      case 'member':
        return 'secondary';
      case 'viewer':
        return 'outline';
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Logo className="w-8 h-8" spinning />
      </div>
    );
  }

  if (!team) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <p className="text-muted-foreground mb-4">Zespół nie został znaleziony</p>
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Powrót do listy
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
        {/* Header */}
        <PageHeader
          title={team.name}
          subtitle={team.description || 'Szczegóły zespołu'}
          actions={
            <div className="flex items-center gap-2">
              <Button onClick={onBack} variant="outline" className="gap-2">
                <ArrowLeft className="w-4 h-4" />
                Powrót
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="icon">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setShowEditDialog(true)}>
                    <Edit className="w-4 h-4 mr-2" />
                    Edytuj Zespół
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={handleDeleteTeam}
                    className="text-destructive"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Usuń Zespół
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          }
        />

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Członkowie</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{team.member_count || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                aktywnych użytkowników
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Projekty</CardTitle>
              <Folder className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{team.project_count || 0}</div>
              <p className="text-xs text-muted-foreground mt-1">
                aktywnych projektów
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <Badge variant={team.is_active ? 'default' : 'secondary'}>
                {team.is_active ? 'Aktywny' : 'Nieaktywny'}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Utworzono: {formatDate(team.created_at)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main content: Members + Context */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Members */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Członkowie Zespołu</CardTitle>
                <Button onClick={() => setShowMembersDialog(true)} className="gap-2">
                  <UserPlus className="w-4 h-4" />
                  Zarządzaj Członkami
                </Button>
              </CardHeader>
              <CardContent>
                {team.members && team.members.length > 0 ? (
                  <div className="space-y-4">
                    {team.members.map((member: TeamMember) => (
                      <div
                        key={member.user_id}
                        className="flex items-center justify-between p-4 border rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Avatar>
                            <AvatarFallback>{getInitials(member.full_name)}</AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{member.full_name}</div>
                            <div className="text-sm text-muted-foreground">{member.email}</div>
                            <div className="text-xs text-muted-foreground mt-1">
                              Dołączył: {formatDate(member.joined_at)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={getRoleBadgeVariant(member.role_in_team)}
                            className="gap-1.5"
                          >
                            {getRoleIcon(member.role_in_team)}
                            {getRoleLabel(member.role_in_team)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Brak członków w zespole</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Team Context: Environments + Projects */}
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Folder className="h-4 w-4 text-muted-foreground" />
                  Środowiska zespołu
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {environmentsLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Logo className="w-5 h-5" spinning />
                  </div>
                ) : environments.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Brak środowisk. Utwórz pierwsze w sekcji „Środowiska”.
                  </p>
                ) : (
                  environments.slice(0, 3).map((env: Environment) => (
                    <button
                      key={env.id}
                      type="button"
                      className="w-full text-left text-xs px-2 py-1.5 rounded-[6px] hover:bg-muted"
                      onClick={() => {
                        setCurrentEnvironmentId(env.id);
                      }}
                    >
                      <div className="font-medium truncate">{env.name}</div>
                      {env.description && (
                        <div className="text-[11px] text-muted-foreground line-clamp-2">
                          {env.description}
                        </div>
                      )}
                    </button>
                  ))
                )}
                {environments.length > 3 && (
                  <p className="text-[11px] text-muted-foreground">
                    +{environments.length - 3} więcej środowisk
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Folder className="h-4 w-4 text-muted-foreground" />
                  Projekty zespołu
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {projectsLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Logo className="w-5 h-5" spinning />
                  </div>
                ) : projects.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Brak projektów w tym zespole. Utwórz pierwszy w sekcji „Projekty”.
                  </p>
                ) : (
                  projects.slice(0, 4).map((project: Project) => (
                    <button
                      key={project.id}
                      type="button"
                      className="w-full text-left text-xs px-2 py-1.5 rounded-[6px] hover:bg-muted"
                      onClick={() => {
                        setSelectedProject(project);
                        if (project.environment_id) {
                          setCurrentEnvironmentId(project.environment_id);
                        }
                      }}
                    >
                      <div className="font-medium truncate">{project.name}</div>
                      {project.description && (
                        <div className="text-[11px] text-muted-foreground line-clamp-2">
                          {project.description}
                        </div>
                      )}
                    </button>
                  ))
                )}
                {projects.length > 4 && (
                  <p className="text-[11px] text-muted-foreground">
                    +{projects.length - 4} więcej projektów
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <ManageMembersDialog
        team={team}
        open={showMembersDialog}
        onOpenChange={setShowMembersDialog}
      />

      <EditTeamDialog
        team={team}
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
      />
    </div>
  );
}
