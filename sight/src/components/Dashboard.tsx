import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import {
  Users,
  FolderOpen,
  MessageSquare,
  TrendingUp,
  BarChart3,
  Eye,
  Plus,
  Clock,
} from "lucide-react";
import svgPaths from "../imports/svg-ad46epxbus";
import pieSvgPaths from "../imports/svg-unlax8gz8c";

const monthlyActivity = [
  { name: "Jan", personas: 42, surveys: 18, focusGroups: 12 },
  { name: "Feb", personas: 38, surveys: 22, focusGroups: 15 },
  { name: "Mar", personas: 45, surveys: 16, focusGroups: 8 },
  { name: "Apr", personas: 52, surveys: 24, focusGroups: 18 },
  { name: "May", personas: 48, surveys: 19, focusGroups: 14 },
  { name: "Jun", personas: 65, surveys: 28, focusGroups: 22 },
  { name: "Jul", personas: 58, surveys: 25, focusGroups: 19 },
  { name: "Aug", personas: 72, surveys: 31, focusGroups: 25 },
];

const projectDistribution = [
  { name: "Mobile App Launch", value: 35, color: "#F27405" },
  { name: "Product Development", value: 28, color: "#F29F05" },
  { name: "Marketing Research", value: 22, color: "#28a745" },
  { name: "Brand Study", value: 15, color: "#17a2b8" },
];

const recentProjects = [
  {
    id: 1,
    name: "Mobile App Launch Research",
    personas: 25,
    surveys: 3,
    focusGroups: 2,
    progress: 65,
    lastActivity: "2 hours ago",
  },
  {
    id: 2,
    name: "Product Development Study",
    personas: 18,
    surveys: 5,
    focusGroups: 2,
    progress: 100,
    lastActivity: "1 day ago",
  },
  {
    id: 3,
    name: "Marketing Research",
    personas: 32,
    surveys: 2,
    focusGroups: 4,
    progress: 45,
    lastActivity: "3 hours ago",
  },
];

// Custom Bar Chart Component based on Figma design
function CustomBarChart() {
  return (
    <div className="flex gap-[12px] items-end justify-between relative w-full h-[240px] px-4">
      {monthlyActivity.map((month, index) => {
        const totalHeight = 200;
        const maxPersonas = Math.max(
          ...monthlyActivity.map((m) => m.personas),
        );
        const maxSurveys = Math.max(
          ...monthlyActivity.map((m) => m.surveys),
        );
        const maxFocusGroups = Math.max(
          ...monthlyActivity.map((m) => m.focusGroups),
        );

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
          (month.focusGroups / maxFocusGroups) *
            (totalHeight * 0.3),
        );

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

interface DashboardProps {
  onNavigate?: (view: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Dashboard
          </h1>
          <p className="text-muted-foreground">
            Overview of your market research activities across
            all projects
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
            onClick={() => onNavigate?.("projects")}
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
            <div className="text-2xl brand-orange">12</div>
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
            <div className="text-2xl brand-orange">247</div>
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
            <div className="text-2xl brand-orange">18</div>
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
            <div className="text-2xl brand-orange">38</div>
            <p className="text-xs text-muted-foreground">
              +3 completed today
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
                Research Activity
              </CardTitle>
              <p className="text-muted-foreground">
                Monthly breakdown of personas, surveys, and
                focus groups
              </p>
            </CardHeader>
            <CardContent>
              <CustomBarChart />
            </CardContent>
          </Card>
        </div>

        {/* Project Distribution */}
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
            <CustomPieChart />
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-[#F27405]" />
                <span className="text-sm text-card-foreground">
                  Mobile App Launch
                </span>
                <span className="text-sm text-muted-foreground ml-auto">
                  35%
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-[#F29F05]" />
                <span className="text-sm text-card-foreground">
                  Product Development
                </span>
                <span className="text-sm text-muted-foreground ml-auto">
                  28%
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-[#28a745]" />
                <span className="text-sm text-card-foreground">
                  Marketing Research
                </span>
                <span className="text-sm text-muted-foreground ml-auto">
                  22%
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-[#17a2b8]" />
                <span className="text-sm text-card-foreground">
                  Brand Study
                </span>
                <span className="text-sm text-muted-foreground ml-auto">
                  15%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card className="bg-card border border-border">
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold text-foreground">
              Recent Projects
            </CardTitle>
            <p className="text-muted-foreground">
              Your latest research projects with detailed
              insights
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-border"
            onClick={() => onNavigate?.("projects")}
          >
            <Eye className="w-4 h-4 mr-2" />
            View All
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentProjects.map((project) => (
              <div
                key={project.id}
                className="p-4 rounded-lg bg-muted/30 border border-border hover:shadow-md transition-shadow"
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
                    className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs"
                    onClick={() => onNavigate?.("projects")}
                  >
                    <Eye className="w-3 h-3 mr-1" />
                    View
                  </Button>
                </div>

                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Personas
                    </p>
                    <p className="text-lg text-card-foreground">
                      {project.personas}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Surveys
                    </p>
                    <p className="text-lg text-card-foreground">
                      {project.surveys}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Focus Groups
                    </p>
                    <p className="text-lg text-card-foreground">
                      {project.focusGroups}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}