/**
 * Environment Summary Card - highlights the current team environment on the dashboard.
 *
 * Uses Zustand store to read currentEnvironmentId and React Query to load environments + projects.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Building2, FolderOpen } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { listEnvironments } from '@/api/environments';
import { projectsApi } from '@/lib/api/projects';
import { useAppStore } from '@/store/appStore';

interface EnvironmentSummaryCardProps {
  onNavigate?: (view: string) => void;
}

export function EnvironmentSummaryCard({ onNavigate }: EnvironmentSummaryCardProps) {
  const { t } = useTranslation('dashboard');
  const currentEnvironmentId = useAppStore((state) => state.currentEnvironmentId);
  const setCurrentEnvironmentId = useAppStore((state) => state.setCurrentEnvironmentId);

  const { data: environments = [], isLoading: isLoadingEnvironments } = useQuery({
    queryKey: ['environments'],
    queryFn: () => listEnvironments(),
  });

  const { data: projects = [], isLoading: isLoadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  const activeEnvironment = useMemo(() => {
    if (!environments.length) return null;
    if (currentEnvironmentId) {
      const matched = environments.find((env) => env.id === currentEnvironmentId);
      if (matched) return matched;
    }
    return environments[0];
  }, [currentEnvironmentId, environments]);

  const environmentProjects = useMemo(() => {
    if (!activeEnvironment) return [];
    return projects.filter((project) => project.environment_id === activeEnvironment.id);
  }, [projects, activeEnvironment]);

  const handleViewEnvironment = () => {
    if (!activeEnvironment) {
      onNavigate?.('environments');
      return;
    }

    setCurrentEnvironmentId(activeEnvironment.id);
    onNavigate?.('environment-detail');
  };

  if (isLoadingEnvironments || isLoadingProjects) {
    return (
      <Card className="border-border rounded-figma-card">
        <CardHeader className="px-6 pt-6 pb-4">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-56 mt-2" />
        </CardHeader>
        <CardContent className="px-6 pb-6 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-10 w-32" />
        </CardContent>
      </Card>
    );
  }

  if (!activeEnvironment) {
    return (
      <Card className="border-border rounded-figma-card">
        <CardHeader className="px-6 pt-6 pb-3">
          <CardTitle className="text-base font-normal text-foreground leading-[16px] flex items-center gap-2">
            <Building2 className="h-5 w-5 text-foreground" />
            {t('environmentSummary.title')}
          </CardTitle>
          <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
            {t('environmentSummary.subtitle')}
          </p>
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <p className="text-sm text-muted-foreground mb-4">
            {t('environmentSummary.noEnvironmentDescription')}
          </p>
          <Button
            variant="outline"
            size="sm"
            className="rounded-figma-button"
            onClick={() => onNavigate?.('environments')}
          >
            {t('environmentSummary.manageEnvironments')}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border rounded-figma-card">
      <CardHeader className="px-6 pt-6 pb-3">
        <CardTitle className="text-base font-normal text-foreground leading-[16px] flex items-center gap-2">
          <Building2 className="h-5 w-5 text-foreground" />
          {t('environmentSummary.title')}
        </CardTitle>
        <p className="text-base text-muted-foreground leading-[24px] mt-1.5">
          {t('environmentSummary.subtitle')}
        </p>
      </CardHeader>
      <CardContent className="px-6 pb-6 space-y-3">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-xs text-muted-foreground uppercase tracking-[0.08em] mb-1">
              {t('environmentSummary.currentEnvironment')}
            </p>
            <p className="text-base text-foreground truncate">{activeEnvironment.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FolderOpen className="h-4 w-4" />
          <span>
            {t('environmentSummary.projectsLabel', {
              count: environmentProjects.length,
            })}
          </span>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="rounded-figma-button mt-2"
          onClick={handleViewEnvironment}
        >
          {t('environmentSummary.viewEnvironment')}
        </Button>
      </CardContent>
    </Card>
  );
}

