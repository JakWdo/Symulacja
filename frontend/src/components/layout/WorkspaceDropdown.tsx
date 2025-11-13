/**
 * Workspace Dropdown Component
 *
 * Hierarchiczny dropdown łączący Środowiska + Projekty
 * Pokazuje aktywne środowisko z badge i listę projektów po rozwinięciu
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Building2, FolderOpen, Plus, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { listEnvironments } from '@/api/environments';
import { projectsApi } from '@/lib/api/projects';
import { getMyTeams } from '@/api/teams';
import {
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';
import { Badge } from '@/components/ui/badge';

interface WorkspaceDropdownProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export function WorkspaceDropdown({ currentView, onNavigate }: WorkspaceDropdownProps) {
  const { t } = useTranslation('common');
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch current team
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: getMyTeams,
  });
  const currentTeam = teamsData?.teams?.[0];

  // Fetch environments
  const { data: environments = [] } = useQuery({
    queryKey: ['environments', currentTeam?.id],
    queryFn: () => listEnvironments(currentTeam?.id),
    enabled: !!currentTeam,
  });

  // Get active environment (first one for now, can be from context later)
  const activeEnvironment = environments.find(env => env.is_active) || environments[0];

  // Fetch projects
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  // Filter projects by active environment
  const environmentProjects = projects.filter(
    project => project.environment_id === activeEnvironment?.id
  );

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
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
        <span className="text-[14px] flex-1">{t('sidebar.workspaces')}</span>
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
        <div className="pl-6 mt-1 space-y-1">
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
  );
}
