/**
 * Workspace Dropdown Component
 *
 * Hierarchiczny dropdown łączący Środowiska + Projekty
 * Pokazuje aktywne środowisko z badge i listę projektów po rozwinięciu
 */

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Building2, FolderOpen, Plus, RefreshCw, Users } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { listEnvironments } from '@/api/environments';
import { projectsApi } from '@/lib/api/projects';
import { getMyTeams } from '@/api/teams';
import {
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';
import { Badge } from '@/components/ui/badge';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
  DrawerClose,
} from '@/components/ui/drawer';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAppStore } from '@/store/appStore';

interface WorkspaceDropdownProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export function WorkspaceDropdown({ currentView, onNavigate }: WorkspaceDropdownProps) {
  const { t } = useTranslation('common');
  const [isExpanded, setIsExpanded] = useState(false);
  const [isTeamDrawerOpen, setIsTeamDrawerOpen] = useState(false);
  const currentTeamId = useAppStore((state) => state.currentTeamId);
  const setCurrentTeamId = useAppStore((state) => state.setCurrentTeamId);
  const currentEnvironmentId = useAppStore((state) => state.currentEnvironmentId);
  const setCurrentEnvironmentId = useAppStore((state) => state.setCurrentEnvironmentId);

  // Fetch current team
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: () => getMyTeams(),
  });

  const teams = teamsData?.teams ?? [];

  // Ustal aktywny zespół na podstawie store lub domyślnie pierwszego
  const currentTeam =
    (currentTeamId && teams.find((team) => team.id === currentTeamId)) ||
    teams[0] ||
    null;

  // Jeśli jeszcze nie wybrano zespołu, a są dostępne, ustaw domyślny
  useEffect(() => {
    if (!currentTeamId && teams.length > 0) {
      setCurrentTeamId(teams[0].id);
    }
  }, [currentTeamId, teams, setCurrentTeamId]);

  // Fetch environments
  const { data: environments = [] } = useQuery({
    queryKey: ['environments', currentTeam?.id],
    queryFn: () => (currentTeam ? listEnvironments(currentTeam.id) : []),
    enabled: !!currentTeam,
  });

  // Get active environment: prefer user selection, fallback to first available
  const activeEnvironment =
    environments.find((env) => env.id === currentEnvironmentId) || environments[0];

  // If there is no selected environment yet but environments are loaded, set default
  useEffect(() => {
    if (!currentEnvironmentId && environments.length > 0) {
      setCurrentEnvironmentId(environments[0].id);
    }
  }, [currentEnvironmentId, environments, setCurrentEnvironmentId]);

  // Fetch projects
  const { data: projects = [] } = useQuery({
    queryKey: ['projects', { teamId: currentTeam?.id }],
    queryFn: () =>
      projectsApi.getAll({
        teamId: currentTeam?.id,
      }),
    enabled: !!currentTeam,
  });

  // Filter projects by active environment (or show all if no environment)
  const environmentProjects = activeEnvironment
    ? projects.filter((project) => project.environment_id === activeEnvironment.id)
    : projects;

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <>
      <SidebarMenuItem>
        <SidebarMenuButton
          onClick={handleToggle}
          className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
            currentView === 'environments' || currentView === 'projects'
              ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
              : 'text-sidebar-foreground hover:bg-sidebar-accent'
          }`}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          <Building2 className="w-4 h-4" />
          <div className="flex-1 flex flex-col text-left">
            <div className="flex items-center justify-between gap-1">
              <span className="text-[14px]">{t('sidebar.workspaces')}</span>
              {teams.length > 1 && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsTeamDrawerOpen(true);
                  }}
                  className="flex items-center gap-1 rounded-[6px] px-2 py-0.5 text-[11px] text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
                >
                  <Users className="w-3 h-3" />
                  <span className="truncate max-w-[80px]">
                    {currentTeam ? currentTeam.name : t('sidebar.teams')}
                  </span>
                </button>
              )}
            </div>
            {!teams.length && (
              <span className="text-[11px] text-muted-foreground truncate">
                {t('sidebar.teams')}
              </span>
            )}
          </div>
          {activeEnvironment && (
            <Badge
              variant="secondary"
              className="text-[10px] px-1.5 py-0 h-5 bg-primary/10 text-primary border-0"
            >
              {activeEnvironment.name}
            </Badge>
          )}
        </SidebarMenuButton>

        {isExpanded && (
          <div className="pl-6 mt-1 space-y-2">
            {/* Projects List */}
          {environmentProjects.length > 0 ? (
            environmentProjects.map((project) => (
              <button
                key={project.id}
                onClick={() => onNavigate('project-detail')}
                className="w-full h-7 flex items-center gap-2 px-2 text-[13px] text-sidebar-foreground hover:bg-sidebar-accent rounded-[6px] transition-colors"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                <span className="truncate">{project.name}</span>
              </button>
            ))
          ) : (
            <div className="h-7 px-2 text-[12px] text-muted-foreground/60 italic">
              {t('sidebar.noProjects')}
            </div>
          )}

            {/* Divider */}
          <div className="h-px bg-sidebar-border my-1" />

            {/* Quick Actions */}
          <button
            onClick={() => onNavigate('projects')}
            className="w-full h-7 flex items-center gap-2 px-2 text-[13px] text-muted-foreground hover:text-foreground hover:bg-sidebar-accent rounded-[6px] transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{t('sidebar.newProject')}</span>
          </button>

          <button
            onClick={() => onNavigate('environments')}
            className="w-full h-7 flex items-center gap-2 px-2 text-[13px] text-muted-foreground hover:text-foreground hover:bg-sidebar-accent rounded-[6px] transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{t('sidebar.changeEnvironment')}</span>
          </button>
          </div>
        )}
      </SidebarMenuItem>

      {/* Team Selector Drawer */}
      <Drawer open={isTeamDrawerOpen} onOpenChange={setIsTeamDrawerOpen}>
        <DrawerContent className="data-[vaul-drawer-direction=right]:w-[320px]">
          <DrawerHeader>
            <DrawerTitle>{t('sidebar.teams')}</DrawerTitle>
            <DrawerDescription>
              Wybierz aktywny zespół, aby filtrować środowiska i projekty.
            </DrawerDescription>
          </DrawerHeader>
          <ScrollArea className="px-4 pb-4 h-[60vh]">
            <div className="space-y-2">
              {teams.map((team) => {
                const isActive = team.id === currentTeam?.id;
                return (
                  <button
                    key={team.id}
                    type="button"
                    onClick={() => {
                      setCurrentTeamId(team.id);
                      setIsTeamDrawerOpen(false);
                    }}
                    className={`w-full flex flex-col items-start gap-1 rounded-[8px] border px-3 py-2 text-left text-[13px] transition-colors ${
                      isActive
                        ? 'border-primary bg-primary/5 text-foreground'
                        : 'border-border text-foreground hover:border-primary/60 hover:bg-sidebar-accent'
                    }`}
                  >
                    <span className="font-medium truncate">{team.name}</span>
                    {team.description && (
                      <span className="text-[11px] text-muted-foreground line-clamp-2">
                        {team.description}
                      </span>
                    )}
                  </button>
                );
              })}
              {!teams.length && (
                <p className="text-[13px] text-muted-foreground">
                  Brak zespołów. Utwórz zespół w widoku „Zespoły”.
                </p>
              )}
            </div>
          </ScrollArea>
          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="outline" className="w-full">
                Zamknij
              </Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
