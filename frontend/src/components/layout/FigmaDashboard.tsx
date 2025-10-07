import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, FolderOpen, Users, BarChart3, MessageSquare, Eye, Clock } from 'lucide-react';
import { projectsApi, personasApi, focusGroupsApi, surveysApi } from '@/lib/api';

interface DashboardProps {
  onNavigate?: (view: string) => void;
}

export function FigmaDashboard({ onNavigate }: DashboardProps) {
  // Fetch all projects
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

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
  });

  // Calculate stats
  const activeProjects = projects.length;
  const totalPersonas = allPersonas.length;
  const runningSurveys = allSurveys.filter(s => s.status === 'running' || s.status === 'completed').length;
  const totalFocusGroups = allFocusGroups.length;

  // Calculate monthly activity
  const monthlyActivity = calculateMonthlyActivity(allPersonas, allSurveys, allFocusGroups);

  // Calculate project distribution
  const projectDistribution = projects.slice(0, 4).map((p, idx) => {
    const projectPersonas = allPersonas.filter(persona => persona.project_id === p.id);
    const total = allPersonas.length || 1;
    const percentage = Math.round((projectPersonas.length / total) * 100);

    return {
      name: p.name,
      percentage,
      color: ['#F27405', '#F29F05', '#28a745', '#17a2b8'][idx % 4],
    };
  });

  // Recent projects
  const recentProjects = projects
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3)
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
        timeAgo = `${hoursDiff} hours ago`;
      } else if (daysDiff === 1) {
        timeAgo = '1 day ago';
      } else {
        timeAgo = `${daysDiff} days ago`;
      }

      return {
        id: project.id,
        name: project.name,
        personas: projectPersonas.length,
        surveys: projectSurveys.length,
        focusGroups: projectFocusGroups.length,
        timeAgo,
      };
    });

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your market research activities across all projects
          </p>
        </div>
        <Button
          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
          onClick={() => onNavigate?.('projects')}
        >
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">Active Projects</CardTitle>
            <FolderOpen className="h-4 w-4 text-[#F27405]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#F27405]">{activeProjects}</div>
            <p className="text-xs text-muted-foreground">+2 from last month</p>
          </CardContent>
        </Card>

        <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Personas</CardTitle>
            <Users className="h-4 w-4 text-[#F27405]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#F27405]">{totalPersonas}</div>
            <p className="text-xs text-muted-foreground">+18% from last month</p>
          </CardContent>
        </Card>

        <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">Running Surveys</CardTitle>
            <BarChart3 className="h-4 w-4 text-[#F27405]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#F27405]">{runningSurveys}</div>
            <p className="text-xs text-muted-foreground">+5 this week</p>
          </CardContent>
        </Card>

        <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">Focus Groups</CardTitle>
            <MessageSquare className="h-4 w-4 text-[#F27405]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#F27405]">{totalFocusGroups}</div>
            <p className="text-xs text-muted-foreground">+3 completed today</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Research Activity Chart */}
        <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl lg:col-span-2 shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-foreground">Research Activity</CardTitle>
            <p className="text-muted-foreground">Monthly breakdown of personas, surveys, and focus groups</p>
          </CardHeader>
          <CardContent>
            <div className="flex gap-[12px] items-end justify-between h-[240px] px-4">
              {monthlyActivity.map((month, index) => {
                const totalHeight = 200;
                const maxPersonas = Math.max(...monthlyActivity.map((m) => m.personas));
                const maxSurveys = Math.max(...monthlyActivity.map((m) => m.surveys));
                const maxFocusGroups = Math.max(...monthlyActivity.map((m) => m.focusGroups));

                const personasHeight = Math.max(
                  20,
                  (month.personas / maxPersonas) * (totalHeight * 0.7),
                );
                const surveysHeight = Math.max(
                  12,
                  (month.surveys / maxSurveys) * (totalHeight * 0.4),
                );
                const focusGroupsHeight = Math.max(
                  8,
                  (month.focusGroups / maxFocusGroups) * (totalHeight * 0.3),
                );

                return (
                  <div key={index} className="flex flex-col items-center gap-3">
                    <div
                      className="bg-[#f3f3f3] flex flex-col items-center justify-end overflow-hidden rounded-[5px] w-[38px]"
                      style={{ height: `${totalHeight}px` }}
                    >
                      <div className="flex-1 bg-[#f2f2f2] w-full" />
                      <div
                        className="bg-[#F27405] w-full"
                        style={{ height: `${personasHeight}px` }}
                      />
                      <div
                        className="bg-[#F29F05] w-full"
                        style={{ height: `${surveysHeight}px` }}
                      />
                      <div
                        className="bg-[#28a745] w-full"
                        style={{ height: `${focusGroupsHeight}px` }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground">{month.name}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Project Distribution */}
        <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-foreground">Project Distribution</CardTitle>
            <p className="text-muted-foreground">Resource allocation by project</p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Pie Chart */}
            <div className="flex items-center justify-center">
              <div className="relative w-[140px] h-[140px] rounded-full border-[20px] border-[#F5F5F5]" style={{
                background: `conic-gradient(
                  #F27405 0% ${projectDistribution[0]?.percentage || 35}%,
                  #F29F05 ${projectDistribution[0]?.percentage || 35}% ${(projectDistribution[0]?.percentage || 35) + (projectDistribution[1]?.percentage || 28)}%,
                  #28a745 ${(projectDistribution[0]?.percentage || 35) + (projectDistribution[1]?.percentage || 28)}% ${(projectDistribution[0]?.percentage || 35) + (projectDistribution[1]?.percentage || 28) + (projectDistribution[2]?.percentage || 22)}%,
                  #17a2b8 ${(projectDistribution[0]?.percentage || 35) + (projectDistribution[1]?.percentage || 28) + (projectDistribution[2]?.percentage || 22)}% 100%
                )`
              }}>
                <div className="absolute inset-[20px] bg-white rounded-full flex items-center justify-center">
                  <span className="text-xl text-muted-foreground">100%</span>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="space-y-3">
              {projectDistribution.map((project, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: project.color }} />
                  <span className="text-sm text-foreground flex-1 truncate">{project.name}</span>
                  <span className="text-sm text-muted-foreground">{project.percentage}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card className="bg-white border border-[rgba(0,0,0,0.12)] rounded-xl shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold text-foreground">Recent Projects</CardTitle>
            <p className="text-muted-foreground">Your latest research projects with detailed insights</p>
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
          {recentProjects.length > 0 ? (
            <div className="space-y-4">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  className="bg-[rgba(248,249,250,0.3)] border border-[rgba(0,0,0,0.12)] rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-medium text-foreground">{project.name}</h4>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                        <Clock className="w-3 h-3" />
                        {project.timeAgo}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      className="bg-[#F27405] hover:bg-[#F27405]/90 text-white text-xs"
                      onClick={() => onNavigate?.('projects')}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      View
                    </Button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-xs text-muted-foreground">Personas</p>
                      <p className="text-lg font-medium text-foreground">{project.personas}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Surveys</p>
                      <p className="text-lg font-medium text-foreground">{project.surveys}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Focus Groups</p>
                      <p className="text-lg font-medium text-foreground">{project.focusGroups}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No projects yet</h3>
              <p className="text-muted-foreground mb-4">Get started by creating your first project</p>
              <Button
                onClick={() => onNavigate?.('projects')}
                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Project
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function calculateMonthlyActivity(personas: any[], surveys: any[], focusGroups: any[]) {
  const now = new Date();
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];

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
