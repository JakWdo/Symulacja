import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Users,
  FolderOpen,
  MessageSquare,
  BarChart3,
  Eye,
  Plus,
  Clock,
} from 'lucide-react';
import { projectsApi, personasApi, focusGroupsApi } from '@/lib/api';
import { pieSvgPaths } from '@/lib/svg-paths';

interface DashboardProps {
  onNavigate?: (view: string) => void;
}

// Custom Bar Chart Component based on Figma design
function CustomBarChart({ data }: { data: any[] }) {
  return (
    <div className="flex gap-[12px] items-end justify-between relative w-full h-[240px] px-4">
      {data.map((month) => {
        const totalHeight = 200;
        const maxPersonas = Math.max(...data.map((m) => m.personas));
        const maxSurveys = Math.max(...data.map((m) => m.surveys));
        const maxFocusGroups = Math.max(...data.map((m) => m.focusGroups));

        const personasHeight = maxPersonas > 0
          ? Math.max(20, (month.personas / maxPersonas) * (totalHeight * 0.7))
          : 0;
        const surveysHeight = maxSurveys > 0
          ? Math.max(12, (month.surveys / maxSurveys) * (totalHeight * 0.4))
          : 0;
        const focusGroupsHeight = maxFocusGroups > 0
          ? Math.max(8, (month.focusGroups / maxFocusGroups) * (totalHeight * 0.3))
          : 0;

        return (
          <div
            key={month.name}
            className="flex flex-col items-center gap-3"
          >
            <div
              className="bg-[#f3f3f3] flex flex-col items-center justify-end overflow-hidden relative rounded-[5px] w-[38px]"
              style={{ height: `${totalHeight}px` }}
            >
              <div className="flex-1 bg-[#f2f2f2] w-full" />
              {personasHeight > 0 && (
                <div
                  className="bg-[#F27405] w-full"
                  style={{ height: `${personasHeight}px` }}
                />
              )}
              {surveysHeight > 0 && (
                <div
                  className="bg-[#F29F05] w-full"
                  style={{ height: `${surveysHeight}px` }}
                />
              )}
              {focusGroupsHeight > 0 && (
                <div
                  className="bg-[#28a745] w-full"
                  style={{ height: `${focusGroupsHeight}px` }}
                />
              )}
            </div>
            <span className="text-sm text-muted-foreground">
              {month.name}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// Custom Pie Chart Component based on Figma design
function CustomPieChart() {
  return (
    <div className="flex items-center justify-center w-full">
      <div className="relative size-[140px] mx-auto">
        <div className="absolute inset-0">
          <svg
            className="block size-full"
            fill="none"
            preserveAspectRatio="none"
            viewBox="0 0 163 163"
          >
            <path d={pieSvgPaths.p3f58c00} fill="#F5F5F5" />
          </svg>
        </div>
        <div className="absolute inset-0">
          <div className="absolute bottom-0 left-0 right-[0.49%] top-[36.73%]">
            <svg
              className="block size-full"
              fill="none"
              preserveAspectRatio="none"
              viewBox="0 0 163 104"
            >
              <path d={pieSvgPaths.p10c7800} fill="#F27405" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-0">
          <div className="absolute bottom-[9.33%] left-0 right-[69.97%] top-[36.34%]">
            <svg
              className="block size-full"
              fill="none"
              preserveAspectRatio="none"
              viewBox="0 0 49 89"
            >
              <path d={pieSvgPaths.p2610ab00} fill="#F29F05" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-0">
          <div className="absolute bottom-0 left-[5.16%] right-[43.49%] top-[63.77%]">
            <svg
              className="block size-full"
              fill="none"
              preserveAspectRatio="none"
              viewBox="0 0 85 60"
            >
              <path d={pieSvgPaths.p27047a40} fill="#28a745" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-0">
          <div className="absolute bottom-0 left-[32.71%] right-[13.45%] top-[74.34%]">
            <svg
              className="block size-full"
              fill="none"
              preserveAspectRatio="none"
              viewBox="0 0 89 42"
            >
              <path d={pieSvgPaths.p13733600} fill="#17a2b8" />
            </svg>
          </div>
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl text-muted-foreground">
            100%
          </span>
        </div>
      </div>
    </div>
  );
}

export function Dashboard({ onNavigate }: DashboardProps) {
  // Fetch projects
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  // Fetch personas across all projects
  const { data: allPersonas = [] } = useQuery({
    queryKey: ['all-personas'],
    queryFn: async () => {
      const personas = await Promise.all(
        projects.map((p) => personasApi.getByProject(p.id))
      );
      return personas.flat();
    },
    enabled: projects.length > 0,
  });

  // Fetch focus groups
  const { data: allFocusGroups = [] } = useQuery({
    queryKey: ['all-focus-groups'],
    queryFn: async () => {
      const fgs = await Promise.all(
        projects.map((p) => focusGroupsApi.getByProject(p.id))
      );
      return fgs.flat();
    },
    enabled: projects.length > 0,
  });

  // Mock monthly activity data (in real app, this would come from API)
  const monthlyActivity = [
    { name: 'Jan', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'Feb', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'Mar', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'Apr', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'May', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'Jun', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'Jul', personas: 0, surveys: 0, focusGroups: 0 },
    { name: 'Aug', personas: allPersonas.length, surveys: 0, focusGroups: allFocusGroups.length },
  ];

  // Calculate project distribution
  const projectDistribution = projects.slice(0, 4).map((p, idx) => ({
    name: p.name,
    value: 100 / Math.max(projects.length, 1),
    color: ['#F27405', '#F29F05', '#28a745', '#17a2b8'][idx % 4],
  }));

  // Recent projects
  const recentProjects = projects
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3)
    .map((project) => ({
      id: project.id,
      name: project.name,
      personas: 0, // Would come from API
      surveys: 0,
      focusGroups: 0,
      progress: 65,
      lastActivity: new Date(project.created_at).toLocaleDateString(),
    }));

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Panel
          </h1>
          <p className="text-muted-foreground">
            Przegląd Twoich działań badawczych we wszystkich projektach
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
            onClick={() => onNavigate?.('projects')}
          >
            <Plus className="w-4 h-4 mr-2" />
            Nowy projekt
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Aktywne projekty
            </CardTitle>
            <FolderOpen className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{projects.length}</div>
            <p className="text-xs text-muted-foreground">
              Wszystkie projekty
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Wszystkie persony
            </CardTitle>
            <Users className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{allPersonas.length}</div>
            <p className="text-xs text-muted-foreground">
              Persony wygenerowane przez AI
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Aktywne ankiety
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">0</div>
            <p className="text-xs text-muted-foreground">
              Bieżące ankiety
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Grupy fokusowe
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl brand-orange">{allFocusGroups.length}</div>
            <p className="text-xs text-muted-foreground">
              Zakończone dyskusje
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Activity Chart */}
        <div className="lg:col-span-2">
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-foreground">
                Aktywność badawcza
              </CardTitle>
              <p className="text-muted-foreground">
                Miesięczny podział person, ankiet i grup fokusowych
              </p>
            </CardHeader>
            <CardContent>
              <CustomBarChart data={monthlyActivity} />
            </CardContent>
          </Card>
        </div>

        {/* Project Distribution */}
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-foreground">
              Rozkład projektów
            </CardTitle>
            <p className="text-muted-foreground">
              Alokacja zasobów według projektu
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <CustomPieChart />
            <div className="space-y-3">
              {projectDistribution.map((project, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: project.color }} />
                  <span className="text-sm text-card-foreground flex-1 truncate">
                    {project.name}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {project.value.toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card className="bg-card border border-border">
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold text-foreground">
              Ostatnie projekty
            </CardTitle>
            <p className="text-muted-foreground">
              Twoje najnowsze projekty badawcze ze szczegółowymi informacjami
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-border"
            onClick={() => onNavigate?.('projects')}
          >
            <Eye className="w-4 h-4 mr-2" />
            Zobacz wszystkie
          </Button>
        </CardHeader>
        <CardContent>
          {recentProjects.length > 0 ? (
            <div className="space-y-4">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  className="p-4 rounded-lg bg-muted/30 border border-border hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onNavigate?.('projects')}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-foreground">
                        {project.name}
                      </h4>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {project.lastActivity}
                      </span>
                    </div>
                    <Button
                      size="sm"
                      className="bg-[#F27405] hover:bg-[#F27405]/90 text-white text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNavigate?.('projects');
                      }}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      Zobacz
                    </Button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        Persony
                      </p>
                      <p className="text-lg text-card-foreground">
                        {project.personas}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        Ankiety
                      </p>
                      <p className="text-lg text-card-foreground">
                        {project.surveys}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        Grupy fokusowe
                      </p>
                      <p className="text-lg text-card-foreground">
                        {project.focusGroups}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">Nie masz jeszcze projektów</h3>
              <p className="text-muted-foreground mb-4">
                Zacznij od utworzenia swojego pierwszego projektu
              </p>
              <Button
                onClick={() => onNavigate?.('projects')}
                className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Utwórz swój pierwszy projekt
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
