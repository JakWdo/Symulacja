/**
 * Active Projects Section - Projects with health status and progress
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, CheckCircle2, Clock, XCircle } from 'lucide-react';
import { useActiveProjects } from '@/hooks/dashboard/useActiveProjects';
import type { ProjectWithHealth } from '@/types/dashboard';

export function ActiveProjectsSection() {
  const { data: projects, isLoading, error } = useActiveProjects();

  if (isLoading) {
    return <ActiveProjectsSkeleton />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Nie udało się załadować aktywnych projektów</AlertDescription>
      </Alert>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Aktywne projekty</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground py-8">
            Brak aktywnych projektów. Stwórz swój pierwszy projekt, aby rozpocząć!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Aktywne projekty</h2>
      <div className="grid gap-4">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
}

function ProjectCard({ project }: { project: ProjectWithHealth }) {
  const healthColors = {
    on_track: 'bg-green-500',
    at_risk: 'bg-yellow-500',
    blocked: 'bg-red-500',
  };

  const statusColors = {
    running: 'bg-blue-500 text-white',
    paused: 'bg-yellow-500 text-white',
    completed: 'bg-green-500 text-white',
    blocked: 'bg-red-500 text-white',
  };

  const StatusIcon = {
    running: Clock,
    paused: AlertTriangle,
    completed: CheckCircle2,
    blocked: XCircle,
  }[project.status];

  const progressPercentage =
    (Number(project.progress.demographics) +
     Number(project.progress.personas) +
     Number(project.progress.focus) +
     Number(project.progress.analysis)) / 4 * 100;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <CardTitle className="text-lg">{project.name}</CardTitle>
              <Badge className={statusColors[project.status]} variant="secondary">
                <StatusIcon className="h-3 w-3 mr-1" />
                {project.status}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${healthColors[project.health.status]}`} />
                Zdrowie: {project.health.score}/100
              </span>
              <span>•</span>
              <span>{project.insights_count} spostrzeżenia</span>
              {project.new_insights_count > 0 && (
                <>
                  <span>•</span>
                  <span className="text-blue-600 font-medium">
                    {project.new_insights_count} nowe
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Progress Bar */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Postęp</span>
            <span>{progressPercentage.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="flex gap-2 text-xs">
            <StageIndicator label="Demografia" completed={project.progress.demographics} />
            <StageIndicator label="Persony" completed={project.progress.personas} />
            <StageIndicator label="Dyskusja" completed={project.progress.focus} />
            <StageIndicator label="Analiza" completed={project.progress.analysis} />
          </div>
        </div>

        {/* Action Button */}
        <Button
          className="w-full"
          onClick={() => window.location.href = project.cta_url}
        >
          {project.cta_label}
        </Button>

        {/* Last Activity */}
        <p className="text-xs text-muted-foreground text-center mt-2">
          Ostatnia aktywność: {new Date(project.last_activity).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  );
}

function StageIndicator({ label, completed }: { label: string; completed: boolean }) {
  return (
    <div className="flex items-center gap-1">
      <div className={`w-2 h-2 rounded-full ${completed ? 'bg-green-500' : 'bg-gray-300'}`} />
      <span className={completed ? 'text-green-600' : 'text-muted-foreground'}>
        {label}
      </span>
    </div>
  );
}

function ActiveProjectsSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-48" />
      <div className="grid gap-4">
        {[...Array(2)].map((_, i) => (
          <Skeleton key={i} className="h-48" />
        ))}
      </div>
    </div>
  );
}
