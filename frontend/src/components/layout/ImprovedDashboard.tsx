/**
 * Improved Dashboard with Charts
 * Migrated from sight/src/components/Dashboard.tsx
 * 
 * Shows overview of ALL projects with:
 * - Stats cards
 * - Monthly activity chart (bar chart)
 * - Project distribution (pie chart)
 * - Recent projects list
 */

import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Users,
  FolderOpen,
  MessageSquare,
  BarChart3,
  Plus,
  Eye,
  Clock,
} from 'lucide-react';
import { projectsApi, personasApi, focusGroupsApi, surveysApi } from '@/lib/api';
import {
  CustomBarChart,
  CustomPieChart,
  ChartLegend,
} from '@/components/charts/CustomCharts';

interface ImprovedDashboardProps {
  onNavigate?: (view: string) => void;
}

export function ImprovedDashboard({ onNavigate }: ImprovedDashboardProps) {
  // Fetch all data
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  const { data: allPersonas = [] } = useQuery({
    queryKey: ['all-personas'],
    queryFn: async () => {
      const allPersonaArrays = await Promise.all(
        projects.map(p => personasApi.getByProject(p.id))
      );
      return allPersonaArrays.flat();
    },
    enabled: projects.length > 0,
  });

  const { data: allFocusGroups = [] } = useQuery({
    queryKey: ['all-focus-groups'],
    queryFn: async () => {
      const allFocusGroupArrays = await Promise.all(
        projects.map(p => focusGroupsApi.getByProject(p.id))
      );
      return allFocusGroupArrays.flat();
    },
    enabled: projects.length > 0,
  });

  const { data: allSurveys = [] } = useQuery({
    queryKey: ['all-surveys'],
    queryFn: async () => {
      const allSurveyArrays = await Promise.all(
        projects.map(p => surveysApi.getByProject(p.id))
      );
      return allSurveyArrays.flat();
    },
    enabled: projects.length > 0,
  });

  // Calculate real stats from data
  const stats = useMemo(() => ({
    activeProjects: projects.length,
    totalPersonas: allPersonas.length,
    runningSurveys: allSurveys.length,
    focusGroups: allFocusGroups.length,
  }), [projects, allPersonas, allSurveys, allFocusGroups]);

  // Calculate monthly activity from created_at dates
  const monthlyActivity = useMemo(() => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const currentYear = new Date().getFullYear();

    return months.map((name, idx) => {
      const personasCount = allPersonas.filter(p => {
        const date = new Date(p.created_at);
        return date.getMonth() === idx && date.getFullYear() === currentYear;
      }).length;

      const surveysCount = allSurveys.filter(s => {
        const date = new Date(s.created_at);
        return date.getMonth() === idx && date.getFullYear() === currentYear;
      }).length;

      const focusGroupsCount = allFocusGroups.filter(fg => {
        const date = new Date(fg.created_at);
        return date.getMonth() === idx && date.getFullYear() === currentYear;
      }).length;

      return {
        name,
        personas: personasCount,
        surveys: surveysCount,
        focusGroups: focusGroupsCount,
      };
    }).slice(0, new Date().getMonth() + 1); // Only show months up to current month
  }, [allPersonas, allSurveys, allFocusGroups]);

  // Calculate project distribution based on persona count
  const projectDistribution = useMemo(() => {
    if (projects.length === 0) return [];

    const colors = ['#F27405', '#F29F05', '#28a745', '#17a2b8'];
    const total = allPersonas.length || 1;

    return projects
      .slice(0, 4) // Top 4 projects
      .map((project, idx) => {
        const projectPersonas = allPersonas.filter(p => p.project_id === project.id).length;
        return {
          name: project.name,
          value: Math.round((projectPersonas / total) * 100),
          color: colors[idx] || '#6f42c1',
        };
      })
      .filter(p => p.value > 0);
  }, [projects, allPersonas]);

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Dashboard
          </h1>
          <p className="text-muted-foreground">
            Overview of your market research activities across all projects
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
            onClick={() => onNavigate?.('projects')}
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Active Projects
            </CardTitle>
            <FolderOpen className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{stats.activeProjects}</div>
            <p className="text-xs text-muted-foreground">
              +2 from last month
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Total Personas
            </CardTitle>
            <Users className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{stats.totalPersonas}</div>
            <p className="text-xs text-muted-foreground">
              +18% from last month
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Running Surveys
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{stats.runningSurveys}</div>
            <p className="text-xs text-muted-foreground">
              +5 this week
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Focus Groups
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{stats.focusGroups}</div>
            <p className="text-xs text-muted-foreground">
              +3 completed today
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid - Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Activity Chart */}
        <div className="lg:col-span-2">
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-foreground">
                Research Activity
              </CardTitle>
              <p className="text-muted-foreground">
                Monthly breakdown of personas, surveys, and focus groups
              </p>
            </CardHeader>
            <CardContent>
              <CustomBarChart data={monthlyActivity} />

              {/* Chart Legend */}
              <div className="mt-6 flex items-center justify-center gap-6 flex-wrap">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-[#F27405]" />
                  <span className="text-sm text-card-foreground">Personas</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-[#F29F05]" />
                  <span className="text-sm text-card-foreground">Surveys</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-[#28a745]" />
                  <span className="text-sm text-card-foreground">Focus Groups</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Project Distribution Pie Chart */}
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-foreground">
              Project Distribution
            </CardTitle>
            <p className="text-muted-foreground">
              Resource allocation by project
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <CustomPieChart data={projectDistribution} />

            {/* Legend */}
            {projectDistribution.length > 0 && (
              <ChartLegend
                items={projectDistribution.map(item => ({
                  name: item.name,
                  color: item.color,
                  percentage: item.value,
                }))}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card className="bg-card border border-border">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold text-foreground">
              Recent Projects
            </CardTitle>
            <p className="text-muted-foreground">
              Your latest research projects with detailed insights
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-border"
            onClick={() => onNavigate?.('projects')}
          >
            <Eye className="w-4 h-4 mr-2" />
            View All
          </Button>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No projects yet</p>
              <Button
                className="mt-4 bg-primary hover:bg-primary/90"
                onClick={() => onNavigate?.('projects')}
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Project
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {projects.slice(0, 3).map((project: any) => (
                <div
                  key={project.id}
                  className="p-4 rounded-lg bg-muted/30 border border-border hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onNavigate?.('projects')}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-foreground font-medium">{project.name}</h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        {project.description}
                      </p>
                      <span className="text-xs text-muted-foreground flex items-center gap-1 mt-2">
                        <Clock className="w-3 h-3" />
                        Created {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <Button
                      size="sm"
                      className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNavigate?.('projects');
                      }}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      View
                    </Button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Personas</p>
                      <p className="text-lg text-card-foreground">
                        {project.target_sample_size || 0}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Surveys</p>
                      <p className="text-lg text-card-foreground">0</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Focus Groups</p>
                      <p className="text-lg text-card-foreground">0</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
