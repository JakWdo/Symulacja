import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, FolderOpen, Users, BarChart3, MessageSquare, Eye, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { projectsApi, personasApi, focusGroupsApi, surveysApi } from '@/lib/api';
import { CustomLineChart, CustomDonutChart, LineChartSeries } from '@/components/charts/CustomCharts';
import { useAppStore } from '@/store/appStore';
import type { Project, Survey, FocusGroup, Persona } from '@/types';
import type { TFunction } from 'i18next';

interface DashboardProps {
  onNavigate?: (view: string) => void;
  onSelectProject?: (project: Project) => void;
}

export function FigmaDashboard({ onNavigate, onSelectProject }: DashboardProps) {
  const { t, i18n } = useTranslation('dashboard');

  // Fetch all projects
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  const { setSelectedProject } = useAppStore();

  const projectIds = projects.map(p => p.id);

  // Fetch all personas
  const { data: allPersonas = [] } = useQuery({
    queryKey: ['personas', 'all', projectIds],
    queryFn: async () => {
      if (projectIds.length === 0) return [];
      const personaArrays = await Promise.all(
        projectIds.map(id => personasApi.getByProject(id).catch(() => []))
      );
      return personaArrays.flat();
    },
    enabled: projectIds.length > 0,
  });

  // Fetch all surveys
  const { data: allSurveys = [] } = useQuery({
    queryKey: ['surveys', 'all', projectIds],
    queryFn: async () => {
      if (projectIds.length === 0) return [];
      const surveyArrays = await Promise.all(
        projectIds.map(id => surveysApi.getByProject(id).catch(() => []))
      );
      return surveyArrays.flat();
    },
    enabled: projectIds.length > 0,
    refetchInterval: (query) => {
      const data = query.state.data as Survey[] | undefined;
      const hasRunning = data?.some((s) => s.status === 'running');
      return hasRunning ? 3000 : false;
    },
  });

  // Fetch all focus groups
  const { data: allFocusGroups = [] } = useQuery({
    queryKey: ['focusGroups', 'all', projectIds],
    queryFn: async () => {
      if (projectIds.length === 0) return [];
      const fgArrays = await Promise.all(
        projectIds.map(id => focusGroupsApi.getByProject(id).catch(() => []))
      );
      return fgArrays.flat();
    },
    enabled: projectIds.length > 0,
    refetchInterval: (query) => {
      const data = query.state.data as FocusGroup[] | undefined;
      const hasRunning = data?.some((fg) => fg.status === 'running');
      return hasRunning ? 2000 : false;
    },
  });

  // Calculate stats
  const activeProjects = projects.length;
  const totalPersonas = allPersonas.length;
  const runningSurveys = allSurveys.filter(s => s.status === 'running' || s.status === 'completed').length;
  const totalFocusGroups = allFocusGroups.length;

  // Calculate monthly activity
  const monthlyActivity = calculateMonthlyActivity(allPersonas, allSurveys, allFocusGroups, t);

  const activitySeries: LineChartSeries[] = [
    {
      id: 'personas',
      label: t('mainDashboard.charts.researchActivity.legend.personas'),
      color: '#F27405',
      getValue: (month) => month.personas,
    },
    {
      id: 'surveys',
      label: t('mainDashboard.charts.researchActivity.legend.surveys'),
      color: '#F29F05',
      getValue: (month) => month.surveys,
    },
    {
      id: 'focusGroups',
      label: t('mainDashboard.charts.researchActivity.legend.focusGroups'),
      color: '#28a745',
      getValue: (month) => month.focusGroups,
    },
  ];

  // Calculate project distribution across recent activity
  const projectActivity = projects.map((project) => {
    const projectPersonas = allPersonas.filter(persona => persona.project_id === project.id);
    const projectSurveys = allSurveys.filter(survey => survey.project_id === project.id);
    const projectFocusGroups = allFocusGroups.filter(fg => fg.project_id === project.id);

    const total =
      projectPersonas.length + projectSurveys.length + projectFocusGroups.length;

    return {
      id: project.id,
      name: project.name,
      personas: projectPersonas.length,
      surveys: projectSurveys.length,
      focusGroups: projectFocusGroups.length,
      total,
    };
  });

  const palette = ['#F27405', '#F29F05', '#28a745', '#17a2b8'];

  const topProjectActivity = projectActivity
    .filter((entry) => entry.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, 4);

  const distributionTotal = topProjectActivity.reduce((sum, entry) => sum + entry.total, 0);

  const projectDistribution = topProjectActivity.map((entry, idx) => {
    const percentage = distributionTotal
      ? Math.round((entry.total / distributionTotal) * 100)
      : 0;

    return {
      name: entry.name,
      value: entry.total,
      color: palette[idx % palette.length],
      percentage,
    };
  });

  // Recent projects
  const recentProjects = [...projects]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 2)
    .map(project => {
      const projectPersonas = allPersonas.filter(p => p.project_id === project.id);
      const projectSurveys = allSurveys.filter(s => s.project_id === project.id);
      const projectFocusGroups = allFocusGroups.filter(fg => fg.project_id === project.id);

      const now = new Date();
      const createdAt = new Date(project.created_at);
      const hoursDiff = Math.floor((now.getTime() - createdAt.getTime()) / (1000 * 60 * 60));
      const daysDiff = Math.floor(hoursDiff / 24);

      let timeAgo = '';
      if (hoursDiff < 24) {
        timeAgo = t('mainDashboard.timeAgo.hoursAgo', { count: hoursDiff });
      } else if (daysDiff === 1) {
        timeAgo = t('mainDashboard.timeAgo.dayAgo');
      } else {
        timeAgo = t('mainDashboard.timeAgo.daysAgo', { count: daysDiff });
      }

      return {
        project,
        personas: projectPersonas.length,
        surveys: projectSurveys.length,
        focusGroups: projectFocusGroups.length,
        timeAgo,
      };
    });

  const handleViewProject = (project: Project) => {
    setSelectedProject(project);
    onSelectProject?.(project);
  };

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">{t('mainDashboard.title')}</h1>
          <p className="text-muted-foreground">
            {t('mainDashboard.subtitle')}
          </p>
        </div>
        <Button
          className="bg-brand hover:bg-brand/90 text-brand-foreground"
          onClick={() => onNavigate?.('projects')}
        >
          <Plus className="w-4 h-4 mr-2" />
          {t('mainDashboard.newProject')}
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-card border border-border rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">{t('mainDashboard.stats.activeProjects')}</CardTitle>
            <FolderOpen className="h-4 w-4 text-brand" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-brand">{activeProjects}</div>
            <p className="text-xs text-muted-foreground">{t('mainDashboard.stats.projectsChange')}</p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">{t('mainDashboard.stats.totalPersonas')}</CardTitle>
            <Users className="h-4 w-4 text-brand" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-brand">{totalPersonas}</div>
            <p className="text-xs text-muted-foreground">{t('mainDashboard.stats.personasChange')}</p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">{t('mainDashboard.stats.runningSurveys')}</CardTitle>
            <BarChart3 className="h-4 w-4 text-brand" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-brand">{runningSurveys}</div>
            <p className="text-xs text-muted-foreground">{t('mainDashboard.stats.surveysChange')}</p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">{t('mainDashboard.stats.focusGroups')}</CardTitle>
            <MessageSquare className="h-4 w-4 text-brand" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-brand">{totalFocusGroups}</div>
            <p className="text-xs text-muted-foreground">{t('mainDashboard.stats.focusGroupsChange')}</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Research Activity Chart */}
        <Card className="bg-card border border-border rounded-xl lg:col-span-2 shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-foreground">{t('mainDashboard.charts.researchActivity.title')}</CardTitle>
            <p className="text-muted-foreground">{t('mainDashboard.charts.researchActivity.subtitle')}</p>
          </CardHeader>
          <CardContent>
            <CustomLineChart data={monthlyActivity} series={activitySeries} />

            {/* Chart Legend */}
            <div className="mt-6 flex items-center justify-center gap-6 flex-wrap">
              {activitySeries.map((serie) => (
                <div key={serie.id} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: serie.color }} />
                  <span className="text-sm text-card-foreground">{serie.label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Project Distribution */}
        <Card className="bg-card border border-border rounded-xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-foreground">{t('mainDashboard.charts.projectDistribution.title')}</CardTitle>
            <p className="text-muted-foreground">{t('mainDashboard.charts.projectDistribution.subtitle')}</p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex w-full justify-center">
              <CustomDonutChart
                data={projectDistribution.map(({ name, value, color }) => ({
                  name,
                  value,
                  color,
                }))}
                totalLabel={t('mainDashboard.charts.projectDistribution.totalLabel')}
              />
            </div>

            {projectDistribution.length > 0 ? (
              <div className="space-y-3">
                {projectDistribution.map((project) => (
                  <div key={project.name} className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded" style={{ backgroundColor: project.color }} />
                    <span className="text-sm text-foreground flex-1 truncate">{project.name}</span>
                    <span className="text-sm text-muted-foreground">{project.percentage}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center">
                {t('mainDashboard.charts.projectDistribution.noData')}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card className="bg-card border border-border rounded-xl shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold text-foreground">{t('mainDashboard.recentProjects.title')}</CardTitle>
            <p className="text-muted-foreground">{t('mainDashboard.recentProjects.subtitle')}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-border"
            onClick={() => onNavigate?.('projects')}
          >
            <Eye className="w-4 h-4 mr-2" />
            {t('mainDashboard.recentProjects.viewAll')}
          </Button>
        </CardHeader>
        <CardContent>
          {recentProjects.length > 0 ? (
            <div className="space-y-4">
              {recentProjects.map(({ project, personas, surveys, focusGroups, timeAgo }) => (
                <div
                  key={project.id}
                  className="bg-muted/30 border border-border rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-medium text-foreground">{project.name}</h4>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                        <Clock className="w-3 h-3" />
                        {timeAgo}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      className="bg-brand hover:bg-brand/90 text-brand-foreground text-xs"
                      onClick={() => handleViewProject(project)}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      {t('mainDashboard.recentProjects.view')}
                    </Button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-xs text-muted-foreground">{t('mainDashboard.recentProjects.personas')}</p>
                      <p className="text-lg font-medium text-foreground">{personas}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t('mainDashboard.recentProjects.surveys')}</p>
                      <p className="text-lg font-medium text-foreground">{surveys}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t('mainDashboard.recentProjects.focusGroups')}</p>
                      <p className="text-lg font-medium text-foreground">{focusGroups}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">{t('mainDashboard.recentProjects.noProjects.title')}</h3>
              <p className="text-muted-foreground mb-4">{t('mainDashboard.recentProjects.noProjects.description')}</p>
              <Button
                onClick={() => onNavigate?.('projects')}
                className="bg-brand hover:bg-brand/90 text-brand-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                {t('mainDashboard.recentProjects.noProjects.createButton')}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  );
}

function calculateMonthlyActivity(personas: Persona[], surveys: Survey[], focusGroups: FocusGroup[], t: TFunction) {
  const now = new Date();
  const months = [
    t('mainDashboard.charts.researchActivity.months.jan'),
    t('mainDashboard.charts.researchActivity.months.feb'),
    t('mainDashboard.charts.researchActivity.months.mar'),
    t('mainDashboard.charts.researchActivity.months.apr'),
    t('mainDashboard.charts.researchActivity.months.may'),
    t('mainDashboard.charts.researchActivity.months.jun'),
    t('mainDashboard.charts.researchActivity.months.jul'),
    t('mainDashboard.charts.researchActivity.months.aug'),
    t('mainDashboard.charts.researchActivity.months.sep'),
    t('mainDashboard.charts.researchActivity.months.oct'),
    t('mainDashboard.charts.researchActivity.months.nov'),
    t('mainDashboard.charts.researchActivity.months.dec')
  ];

  const activity = [];
  for (let i = 7; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const monthName = months[date.getMonth()];

    const personasCount = personas.filter(p => {
      const createdDate = new Date(p.created_at);
      return createdDate.getMonth() === date.getMonth() &&
             createdDate.getFullYear() === date.getFullYear();
    }).length;

    const surveysCount = surveys.filter(s => {
      const createdDate = new Date(s.created_at);
      return createdDate.getMonth() === date.getMonth() &&
             createdDate.getFullYear() === date.getFullYear();
    }).length;

    const focusGroupsCount = focusGroups.filter(fg => {
      const createdDate = new Date(fg.created_at);
      return createdDate.getMonth() === date.getMonth() &&
             createdDate.getFullYear() === date.getFullYear();
    }).length;

    activity.push({
      name: monthName,
      personas: personasCount,
      surveys: surveysCount,
      focusGroups: focusGroupsCount,
    });
  }

  return activity;
}
