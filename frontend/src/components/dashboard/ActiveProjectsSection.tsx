/**
 * Active Projects Section - Figma Make Design
 *
 * Card-based vertical list (no table)
 * - Header: Title + Status Badge + Action Buttons
 * - Meta: Timestamp + Health Indicator
 * - Progress: 4 individual bars (Demographics, Personas, Focus, Analysis)
 * - Footer: Insights count + Alerts
 */

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  Clock,
  Eye,
  Trash2,
  Play,
  Download,
  Lightbulb,
  AlertCircle,
} from 'lucide-react';
import { useActiveProjects } from '@/hooks/dashboard/useActiveProjects';
import type { ProjectWithHealth } from '@/types/dashboard';

export function ActiveProjectsSection({ onNavigate }: { onNavigate?: (view: string) => void }) {
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
      <Card className="border-border rounded-[8px]">
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">
            Brak aktywnych projektów. Utwórz swój pierwszy projekt, aby rozpocząć!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-normal text-foreground leading-[16px]">Aktywne projekty badawcze</h2>
          <p className="text-base text-muted-foreground leading-[24px]">Monitoruj postęp, stan i spostrzeżenia we wszystkich projektach</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="h-8 border-border text-foreground hover:bg-muted/50 rounded-[6px]"
          onClick={() => onNavigate?.('projects')}
        >
          <Eye className="w-4 h-4 mr-2" />
          Zobacz wszystkie
        </Button>
      </div>

      {/* Projects List (Cards) */}
      <div className="space-y-4">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
}

// ========== PROJECT CARD (Figma Design) ==========

function ProjectCard({ project }: { project: ProjectWithHealth }) {
  // Status badge - outline only (from Figma)
  const statusConfig = {
    running: {
      color: 'border-border text-foreground',
      dotColor: 'bg-[#28a745]',
      label: 'W trakcie',
    },
    blocked: {
      color: 'border-border text-foreground',
      dotColor: 'bg-[#fb2c36]',
      label: 'Zablokowany',
    },
    paused: {
      color: 'border-border text-foreground',
      dotColor: 'bg-[#ffc107]',
      label: 'Wstrzymany',
    },
    completed: {
      color: 'border-border text-foreground',
      dotColor: 'bg-[#28a745]',
      label: 'Ukończony',
    },
  };

  // Health indicator colors (correct Figma red)
  const healthConfig = {
    on_track: {
      color: 'bg-[#28a745]',
      label: 'Na bieżąco',
    },
    at_risk: {
      color: 'bg-[#ffc107]',
      label: 'Zagrożony',
    },
    blocked: {
      color: 'bg-[#fb2c36]',
      label: 'Zablokowany',
    },
  };

  const status = statusConfig[project.status] || statusConfig.running;
  const health = healthConfig[project.health.status] || healthConfig.on_track;

  // Format timestamp
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return 'Teraz';
    if (diffHours < 24) return `${diffHours} godz. temu`;
    if (diffDays === 1) return '1 dzień temu';
    return `${diffDays} dni temu`;
  };

  // Get action button for status
  const getActionButton = () => {
    switch (project.status) {
      case 'blocked':
        return (
          <Button
            size="sm"
            className="bg-red-500/5 dark:bg-red-500/10 border border-red-500/20 dark:border-red-500/30 text-foreground h-8 rounded-[6px]"
            onClick={() => window.location.href = project.cta_url}
          >
            <AlertCircle className="w-4 h-4 mr-2" />
            Napraw problemy
          </Button>
        );
      case 'paused':
        return (
          <Button
            size="sm"
            className="bg-figma-primary hover:bg-figma-primary/90 text-white h-8 rounded-[6px]"
            onClick={() => window.location.href = project.cta_url}
          >
            <Play className="w-4 h-4 mr-2" />
            Wznów
          </Button>
        );
      case 'completed':
        return (
          <Button
            size="sm"
            className="bg-figma-primary hover:bg-figma-primary/90 text-white h-8 rounded-[6px]"
            onClick={() => window.location.href = project.cta_url}
          >
            <Download className="w-4 h-4 mr-2" />
            Eksportuj
          </Button>
        );
      default:
        return null;
    }
  };

  // Convert boolean progress to percentage
  const progressToPercentage = (value: boolean): number => (value ? 100 : 0);

  // Get alert message (if any)
  const getAlert = () => {
    if (project.status === 'blocked' && !project.progress.personas) {
      return {
        icon: AlertCircle,
        text: `Low persona coverage (${progressToPercentage(project.progress.personas)}%)`,
      };
    }
    if (project.health.status === 'at_risk') {
      // Check for idle focus group (this is mock data, adjust based on your API)
      return {
        icon: Clock,
        text: 'Grupa fokusowa bezczynna od 52 godz.',
      };
    }
    return null;
  };

  const alert = getAlert();

  return (
    <Card className="border-border rounded-[8px]">
      <CardContent className="p-[17px]">
        {/* Header Row */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <h3 className="text-base font-normal text-foreground leading-[24px]">
              {project.name}
            </h3>
            {/* Status Indicator Dot */}
            <div className={`w-2 h-2 rounded-full ${status.dotColor}`} />
            {/* Status Badge - outline only */}
            <Badge variant="outline" className={`border ${status.color} text-xs font-semibold rounded-[6px] capitalize`}>
              {status.label}
            </Badge>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {getActionButton()}
            <Button
              variant="outline"
              size="sm"
              className="h-8 w-8 p-0 border-border rounded-[6px]"
              onClick={() => window.location.href = project.cta_url}
            >
              <Eye className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 w-8 p-0 border-border rounded-[6px]"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Meta Row */}
        <div className="flex items-center gap-2 mb-3 text-xs text-muted-foreground">
          <Clock className="w-3 h-3" />
          <span>{formatTimeAgo(project.last_activity)}</span>
          <span>•</span>
          <div className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded-full ${health.color}`} />
            <span className="capitalize">{health.label}</span>
          </div>
        </div>

        {/* Progress Bars (4 columns grid - horizontal layout from Figma) */}
        <div className="grid grid-cols-4 gap-3 mb-3">
          <ProgressBar
            label="Demografia"
            percentage={progressToPercentage(project.progress.demographics)}
          />
          <ProgressBar
            label="Persony"
            percentage={progressToPercentage(project.progress.personas)}
          />
          <ProgressBar
            label="Grupa fokusowa"
            percentage={progressToPercentage(project.progress.focus)}
          />
          <ProgressBar
            label="Analiza"
            percentage={progressToPercentage(project.progress.analysis)}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between h-5">
          {/* Insights Count */}
          <div className="flex items-center gap-1.5 text-sm text-foreground">
            <Lightbulb className="w-4 h-4 text-figma-primary" />
            <span>
              {project.new_insights_count > 0 && (
                <span className="font-semibold text-figma-primary">
                  +{project.new_insights_count}{' '}
                </span>
              )}
              {project.insights_count} spostrzeżeń
            </span>
          </div>

          {/* Alert (if any) */}
          {alert && (
            <div className="flex items-center gap-1 text-xs text-[#dc3545]">
              <alert.icon className="w-3 h-3" />
              <span>{alert.text}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ========== PROGRESS BAR COMPONENT (Figma: vertical stack) ==========

function ProgressBar({ label, percentage }: { label: string; percentage: number }) {
  return (
    <div className="flex flex-col gap-1">
      {/* Label + Percentage Row */}
      <div className="flex items-center justify-between h-4">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs text-foreground">{percentage}%</span>
      </div>

      {/* Progress Bar */}
      <div className="h-[6px] bg-orange-500/20 dark:bg-orange-500/30 rounded-full overflow-hidden">
        <div
          className="h-full bg-figma-primary transition-all duration-300 rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// ========== SKELETON ==========

function ActiveProjectsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-8 w-24" />
      </div>
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-40 rounded-[8px]" />
        ))}
      </div>
    </div>
  );
}
