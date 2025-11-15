import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/layout/PageHeader';
import { Logo } from '@/components/ui/logo';
import { FacetedFilters } from './FacetedFilters';
import { getEnvironment, listEnvironments } from '@/api/environments';
import { projectsApi } from '@/lib/api/projects';
import type { Project } from '@/types';
import { useAppStore } from '@/store/appStore';
import { Calendar, Folder, Users } from 'lucide-react';
import { formatDate } from '@/lib/utils';

interface EnvironmentDetailProps {
  onBack: () => void;
}

export function EnvironmentDetail({ onBack }: EnvironmentDetailProps) {
  const { t } = useTranslation('common');
  const currentTeamId = useAppStore((state) => state.currentTeamId);
  const currentEnvironmentId = useAppStore((state) => state.currentEnvironmentId);

  const { data: environments = [] } = useQuery({
    queryKey: ['environments', currentTeamId],
    queryFn: () => listEnvironments(currentTeamId ?? undefined),
  });

  const environment = useMemo(
    () => environments.find((env) => env.id === currentEnvironmentId) ?? null,
    [environments, currentEnvironmentId],
  );

  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects', { environmentId: currentEnvironmentId }],
    queryFn: () =>
      projectsApi.getAll({
        environmentId: currentEnvironmentId ?? undefined,
      }),
  });

  const environmentProjects: Project[] = useMemo(
    () =>
      environment
        ? projects.filter((p) => p.environment_id === environment.id)
        : [],
    [projects, environment],
  );

  if (!currentEnvironmentId || !environment) {
    return (
      <div className="w-full h-full flex items-center justify-center flex-col gap-4">
        <Logo className="w-8 h-8" />
        <p className="text-sm text-muted-foreground">
          {t('environments.noSelectedEnvironment')}
        </p>
        <Button variant="outline" onClick={onBack}>
          {t('environments.backToList')}
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
        <PageHeader
          title={environment.name}
          subtitle={t('environments.subtitle')}
          actions={
            <Button variant="outline" onClick={onBack}>
              {t('environments.backToEnvironments')}
            </Button>
          }
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column: Environment meta + projects */}
          <div className="space-y-4 lg:col-span-1">
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  {t('environments.details')}
                  <Badge variant="outline">{t('environments.current')}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {environment.description && (
                  <p className="text-sm text-muted-foreground">
                    {environment.description}
                  </p>
                )}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Calendar className="w-3 h-3" />
                  <span>{t('environments.created')} {formatDate(environment.created_at)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Users className="w-3 h-3" />
                  <span>Team ID: {environment.team_id}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Folder className="w-4 h-4" />
                  {t('environments.projectsInEnvironment')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {projectsLoading ? (
                  <div className="flex items-center justify-center py-6">
                    <Logo className="w-6 h-6" spinning />
                  </div>
                ) : environmentProjects.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    {t('environments.noProjectsInEnvironment')}
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {environmentProjects.map((project) => (
                      <li
                        key={project.id}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="truncate">{project.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(project.created_at)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right column: Faceted filters */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <CardTitle>Eksploruj zasoby w tej bibliotece</CardTitle>
              </CardHeader>
              <CardContent>
                <FacetedFilters
                  environmentId={environment.id}
                  resourceType="persona"
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
