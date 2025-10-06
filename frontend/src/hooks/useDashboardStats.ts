import { useQuery } from '@tanstack/react-query';
import { projectsApi, personasApi, focusGroupsApi } from '@/lib/api';

interface DashboardStats {
  totalProjects: number;
  activeProjects: number;
  totalPersonas: number;
  totalFocusGroups: number;
  completedFocusGroups: number;
  projectsChange: string;
  personasChange: string;
}

interface MonthlyActivity {
  name: string;
  value: number;
}

export function useDashboardStats() {
  // Fetch all projects
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  // Aggregate stats
  const stats: DashboardStats = {
    totalProjects: projects.length,
    activeProjects: projects.filter(p => p.is_active).length,
    totalPersonas: 0,
    totalFocusGroups: 0,
    completedFocusGroups: 0,
    projectsChange: '+0%',
    personasChange: '+0%',
  };

  // Fetch personas and focus groups for each project
  const projectIds = projects.map(p => p.id);

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

  stats.totalPersonas = allPersonas.length;
  stats.totalFocusGroups = allFocusGroups.length;
  stats.completedFocusGroups = allFocusGroups.filter(
    fg => fg.status === 'completed'
  ).length;

  // Calculate monthly activity (personas created per month)
  const monthlyActivity: MonthlyActivity[] = calculateMonthlyActivity(allPersonas);

  // Calculate recent projects (last 5)
  const recentProjects = projects
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)
    .map(project => {
      const projectPersonas = allPersonas.filter(p => p.project_id === project.id);
      const projectFocusGroups = allFocusGroups.filter(fg => fg.project_id === project.id);

      return {
        id: project.id,
        name: project.name,
        status: mapStatus(project.is_active),
        personas: projectPersonas.length,
        groups: projectFocusGroups.length,
      };
    });

  return {
    stats,
    monthlyActivity,
    recentProjects,
    isLoading: projectsLoading,
  };
}

function calculateMonthlyActivity(personas: any[]): MonthlyActivity[] {
  const now = new Date();
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  // Last 6 months
  const activity: MonthlyActivity[] = [];
  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const monthName = months[date.getMonth()];
    const count = personas.filter(p => {
      const createdDate = new Date(p.created_at);
      return createdDate.getMonth() === date.getMonth() &&
             createdDate.getFullYear() === date.getFullYear();
    }).length;

    activity.push({ name: monthName, value: count });
  }

  return activity;
}

function mapStatus(isActive: boolean): string {
  return isActive ? 'Active' : 'Completed';
}
