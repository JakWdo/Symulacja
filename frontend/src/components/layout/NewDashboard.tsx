import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { Users, FolderOpen, MessageSquare, TrendingUp } from 'lucide-react';
import { useDashboardStats } from '@/hooks/useDashboardStats';

export function NewDashboard() {
  const { stats, monthlyActivity, recentProjects, isLoading } = useDashboardStats();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active':
        return 'bg-[rgba(37,99,235,0.2)] text-blue-600 border-[rgba(37,99,235,0.3)]';
      case 'Completed':
        return 'bg-[rgba(255,109,46,0.2)] text-[#ff6d2e] border-[rgba(255,109,46,0.3)]';
      case 'In Progress':
        return 'bg-[rgba(139,92,246,0.2)] text-violet-500 border-[rgba(139,92,246,0.3)]';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 size-full">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-[30px] font-semibold leading-9 text-foreground">Dashboard</h1>
        <p className="text-[16px] leading-6 text-muted-foreground">Overview of your market research activities</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-[146px]">
        <Card className="bg-card border border-border rounded-[14px] flex flex-col gap-6 p-px">
          <CardHeader className="flex flex-row items-center justify-between h-12 px-6 py-0">
            <CardTitle className="text-[16px] leading-4 tracking-[-0.4px] text-card-foreground/80">
              Active Projects
            </CardTitle>
            <FolderOpen className="h-4 w-4 text-chart-1" />
          </CardHeader>
          <CardContent className="flex-1 flex flex-col px-6 py-0">
            <div className="text-[24px] leading-8 font-bold text-card-foreground">
              {isLoading ? '...' : stats.activeProjects}
            </div>
            <p className="text-[12px] leading-4 text-muted-foreground">
              {stats.totalProjects} total projects
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border rounded-[14px] flex flex-col gap-6 p-px">
          <CardHeader className="flex flex-row items-center justify-between h-12 px-6 py-0">
            <CardTitle className="text-[16px] leading-4 tracking-[-0.4px] text-card-foreground/80">
              Generated Personas
            </CardTitle>
            <Users className="h-4 w-4 text-chart-4" />
          </CardHeader>
          <CardContent className="flex-1 flex flex-col px-6 py-0">
            <div className="text-[24px] leading-8 font-bold text-card-foreground">
              {isLoading ? '...' : stats.totalPersonas}
            </div>
            <p className="text-[12px] leading-4 text-muted-foreground">
              Across all projects
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border rounded-[14px] flex flex-col gap-6 p-px">
          <CardHeader className="flex flex-row items-center justify-between h-12 px-6 py-0">
            <CardTitle className="text-[16px] leading-4 tracking-[-0.4px] text-card-foreground/80">
              Focus Groups
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-chart-2" />
          </CardHeader>
          <CardContent className="flex-1 flex flex-col px-6 py-0">
            <div className="text-[24px] leading-8 font-bold text-card-foreground">
              {isLoading ? '...' : stats.totalFocusGroups}
            </div>
            <p className="text-[12px] leading-4 text-muted-foreground">
              {stats.completedFocusGroups} completed
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border rounded-[14px] flex flex-col gap-6 p-px">
          <CardHeader className="flex flex-row items-center justify-between h-12 px-6 py-0">
            <CardTitle className="text-[16px] leading-4 tracking-[-0.4px] text-card-foreground/80">
              Completion Rate
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-chart-5" />
          </CardHeader>
          <CardContent className="flex-1 flex flex-col px-6 py-0">
            <div className="text-[24px] leading-8 font-bold text-card-foreground">
              {isLoading ? '...' : stats.totalFocusGroups > 0
                ? Math.round((stats.completedFocusGroups / stats.totalFocusGroups) * 100) + '%'
                : '0%'
              }
            </div>
            <p className="text-[12px] leading-4 text-muted-foreground">
              Focus group success
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[376px]">
        {/* Stats Chart */}
        <Card className="bg-card border border-border rounded-[14px] relative">
          <CardHeader className="pt-6 px-6 pb-0">
            <CardTitle className="text-[16px] leading-4 text-card-foreground">Monthly Activity</CardTitle>
            <p className="text-[16px] leading-6 text-muted-foreground mt-[6px]">Generated personas over time</p>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-64 bg-card border border-border rounded-[10px] p-4 m-6 mt-[24px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyActivity} barCategoryGap="20%">
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }}
                  />
                  <Bar
                    dataKey="value"
                    fill="hsl(var(--foreground))"
                    radius={[8, 8, 0, 0]}
                    maxBarSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Recent Projects */}
        <Card className="bg-card border border-border rounded-[14px] relative">
          <CardHeader className="pt-6 px-6 pb-0">
            <CardTitle className="text-[16px] leading-4 text-card-foreground">Recent Projects</CardTitle>
            <p className="text-[16px] leading-6 text-muted-foreground mt-[6px]">Your latest research projects</p>
          </CardHeader>
          <CardContent className="p-6 pt-[24px]">
            <div className="flex flex-col gap-4">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  className="flex items-center justify-between h-[70px] px-[13px] py-px bg-sidebar-accent border border-border rounded-[10px]"
                >
                  <div className="flex-1 flex flex-col gap-1">
                    <h4 className="text-[16px] leading-6 font-medium text-card-foreground">{project.name}</h4>
                    <div className="flex items-center gap-4">
                      <span className="text-[12px] leading-4 text-muted-foreground">{project.personas} personas</span>
                      <span className="text-[12px] leading-4 text-muted-foreground">{project.groups} groups</span>
                    </div>
                  </div>
                  <Badge className={`${getStatusColor(project.status)} h-[22px] rounded-[8px] px-[9px] py-[3px] text-[12px] leading-4 font-medium border`}>
                    {project.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
