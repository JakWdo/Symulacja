import { useState, useMemo, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "./ui/card";
import { Button } from "./ui/button";
import {
  Users,
  FolderOpen,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Eye,
  Plus,
  Clock,
  AlertCircle,
  CheckCircle2,
  Pause,
  Play,
  Archive,
  Zap,
  Target,
  Lightbulb,
  AlertTriangle,
  DollarSign,
  Activity,
  ChevronRight,
  Bell,
  Shield,
  XCircle,
  Settings,
  Download,
  Share2,
  Sparkles,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Skeleton } from "./ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { toast } from "sonner@2.0.3";
import { Separator } from "./ui/separator";

// Types & Interfaces
interface ProjectHealth {
  status: "on-track" | "at-risk" | "blocked";
  blockers: string[];
}

interface Project {
  id: string;
  name: string;
  status: "running" | "paused" | "completed" | "blocked";
  health: ProjectHealth;
  progress: {
    demographics: number;
    personas: number;
    focus: number;
    analysis: number;
  };
  insights: {
    new: number;
    total: number;
  };
  lastActivity: string;
  lastActivityTime: Date;
}

interface Insight {
  id: string;
  type: "opportunity" | "risk" | "trend";
  title: string;
  description: string;
  confidence: number;
  impact: "high" | "medium" | "low";
  timestamp: Date;
  projectId: string;
  projectName: string;
  evidence: string[];
  source: string;
}

interface Notification {
  id: string;
  type: "insight-ready" | "focus-idle" | "confidence-drop" | "low-coverage" | "budget-alert";
  title: string;
  description: string;
  timestamp: Date;
  priority: "high" | "medium" | "low";
  read: boolean;
  actionable: boolean;
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  priority: "critical" | "high" | "medium" | "low";
  type: "fix-issues" | "generate-personas" | "start-focus" | "view-insights" | "new-research";
  projectId?: string;
  projectName?: string;
  action: (onNavigate?: (view: string) => void) => void;
}

interface KPIMetrics {
  timeToInsight: {
    median: number;
    p90: number;
    trend: number;
    unit: "hours";
  };
  insightAdoptionRate: {
    current: number;
    trend: number;
    target: number;
  };
  activeProjects: {
    running: number;
    blocked: number;
    paused: number;
    completed: number;
  };
  personaCoverage: {
    current: number;
    target: number;
    gapSegments: string[];
  };
  weeklyActivity: {
    personas: number;
    focusGroups: number;
    insights: number;
    trend: number;
  };
}

interface UsageMetrics {
  tokens: number;
  cost: number;
  budget: number;
  forecast: number;
  threshold: number;
}

// Mock Data Service
class DashboardService {
  static getKPIMetrics(): KPIMetrics {
    return {
      timeToInsight: {
        median: 4.2,
        p90: 8.5,
        trend: -12.5, // -12.5% improvement
        unit: "hours",
      },
      insightAdoptionRate: {
        current: 47,
        trend: 8.3,
        target: 60,
      },
      activeProjects: {
        running: 8,
        blocked: 2,
        paused: 3,
        completed: 5,
      },
      personaCoverage: {
        current: 78,
        target: 90,
        gapSegments: ["Gen Z Urban", "Rural 55+", "Small Business Owners"],
      },
      weeklyActivity: {
        personas: 42,
        focusGroups: 8,
        insights: 23,
        trend: 15.2,
      },
    };
  }

  static getProjects(): Project[] {
    const now = new Date();
    return [
      {
        id: "1",
        name: "Mobile App Launch Research",
        status: "running",
        health: { status: "on-track", blockers: [] },
        progress: { demographics: 100, personas: 100, focus: 75, analysis: 60 },
        insights: { new: 5, total: 12 },
        lastActivity: "2 hours ago",
        lastActivityTime: new Date(now.getTime() - 2 * 60 * 60 * 1000),
      },
      {
        id: "2",
        name: "Product Development Study",
        status: "blocked",
        health: {
          status: "blocked",
          blockers: ["Low persona coverage (45%)", "Analysis failed - retry needed"],
        },
        progress: { demographics: 100, personas: 45, focus: 0, analysis: 0 },
        insights: { new: 0, total: 3 },
        lastActivity: "1 day ago",
        lastActivityTime: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      },
      {
        id: "3",
        name: "Marketing Campaign Analysis",
        status: "running",
        health: {
          status: "at-risk",
          blockers: ["Focus group idle for 52h"],
        },
        progress: { demographics: 100, personas: 100, focus: 40, analysis: 20 },
        insights: { new: 2, total: 8 },
        lastActivity: "5 hours ago",
        lastActivityTime: new Date(now.getTime() - 5 * 60 * 60 * 1000),
      },
      {
        id: "4",
        name: "Brand Perception Research",
        status: "paused",
        health: { status: "on-track", blockers: [] },
        progress: { demographics: 100, personas: 100, focus: 100, analysis: 85 },
        insights: { new: 0, total: 15 },
        lastActivity: "3 days ago",
        lastActivityTime: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000),
      },
      {
        id: "5",
        name: "User Experience Study",
        status: "completed",
        health: { status: "on-track", blockers: [] },
        progress: { demographics: 100, personas: 100, focus: 100, analysis: 100 },
        insights: { new: 8, total: 28 },
        lastActivity: "1 day ago",
        lastActivityTime: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      },
    ];
  }

  static getInsights(): Insight[] {
    const now = new Date();
    return [
      {
        id: "i1",
        type: "opportunity",
        title: "Strong positive sentiment for premium features",
        description: "87% of personas in high-income segment show willingness to pay for advanced analytics",
        confidence: 92,
        impact: "high",
        timestamp: new Date(now.getTime() - 3 * 60 * 60 * 1000),
        projectId: "1",
        projectName: "Mobile App Launch Research",
        evidence: [
          '"I would definitely pay extra for better insights" - Persona #12',
          '"Advanced features are worth the investment" - Persona #8',
          '"Premium tier makes sense for power users" - Persona #23',
        ],
        source: "Focus Group Session #3, GPT-4o, Prompt v2.1",
      },
      {
        id: "i2",
        type: "risk",
        title: "Privacy concerns may impact adoption",
        description: "65% express concerns about data collection practices in initial onboarding",
        confidence: 78,
        impact: "high",
        timestamp: new Date(now.getTime() - 5 * 60 * 60 * 1000),
        projectId: "1",
        projectName: "Mobile App Launch Research",
        evidence: [
          '"Not sure I trust giving all this data" - Persona #5',
          '"Privacy policy is unclear" - Persona #19',
        ],
        source: "Survey Analysis, GPT-4o, Prompt v2.1",
      },
      {
        id: "i3",
        type: "trend",
        title: "Rising interest in sustainability features",
        description: "Month-over-month increase of 34% in mentions of eco-friendly options",
        confidence: 85,
        impact: "medium",
        timestamp: new Date(now.getTime() - 8 * 60 * 60 * 1000),
        projectId: "3",
        projectName: "Marketing Campaign Analysis",
        evidence: [
          '"Sustainability is a key factor for me" - Persona #7',
          '"I prefer brands that care about environment" - Persona #14',
        ],
        source: "Focus Group Session #5, GPT-4o, Prompt v2.1",
      },
      {
        id: "i4",
        type: "opportunity",
        title: "Untapped segment: Remote workers",
        description: "Remote workers show 2.3x higher engagement but only 12% coverage in current research",
        confidence: 88,
        impact: "high",
        timestamp: new Date(now.getTime() - 12 * 60 * 60 * 1000),
        projectId: "5",
        projectName: "User Experience Study",
        evidence: [
          '"As a remote worker, I need better collaboration tools" - Persona #31',
          '"Working from home changed my priorities" - Persona #42',
        ],
        source: "Persona Analysis, GPT-4o, Prompt v2.0",
      },
    ];
  }

  static getNotifications(): Notification[] {
    const now = new Date();
    return [
      {
        id: "n1",
        type: "insight-ready",
        title: "5 new insights ready for review",
        description: "Mobile App Launch Research generated new insights with high confidence",
        timestamp: new Date(now.getTime() - 30 * 60 * 1000),
        priority: "high",
        read: false,
        actionable: true,
      },
      {
        id: "n2",
        type: "focus-idle",
        title: "Focus group idle for 52 hours",
        description: "Marketing Campaign Analysis - focus group not resumed",
        timestamp: new Date(now.getTime() - 52 * 60 * 60 * 1000),
        priority: "medium",
        read: false,
        actionable: true,
      },
      {
        id: "n3",
        type: "budget-alert",
        title: "Budget threshold at 92%",
        description: "Monthly token budget nearly exhausted, consider optimization",
        timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000),
        priority: "high",
        read: false,
        actionable: true,
      },
      {
        id: "n4",
        type: "low-coverage",
        title: "Persona coverage below target",
        description: "Product Development Study at 45% coverage, 55% gap detected",
        timestamp: new Date(now.getTime() - 4 * 60 * 60 * 1000),
        priority: "medium",
        read: true,
        actionable: true,
      },
    ];
  }

  static getUsageMetrics(): UsageMetrics {
    return {
      tokens: 4_600_000,
      cost: 92.5,
      budget: 100,
      forecast: 98.3,
      threshold: 90,
    };
  }

  static getWeeklyTrend() {
    return [
      { day: "Mon", personas: 12, focusGroups: 2, insights: 5 },
      { day: "Tue", personas: 8, focusGroups: 1, insights: 3 },
      { day: "Wed", personas: 15, focusGroups: 3, insights: 7 },
      { day: "Thu", personas: 10, focusGroups: 2, insights: 6 },
      { day: "Fri", personas: 18, focusGroups: 4, insights: 9 },
      { day: "Sat", personas: 5, focusGroups: 0, insights: 2 },
      { day: "Sun", personas: 7, focusGroups: 1, insights: 3 },
    ];
  }

  static getInsightTypesDistribution() {
    return [
      { name: "Opportunities", value: 45, color: "#28a745" },
      { name: "Risks", value: 30, color: "#dc3545" },
      { name: "Trends", value: 25, color: "#F29F05" },
    ];
  }

  static getTopConcepts() {
    return [
      { concept: "Privacy & Security", count: 142 },
      { concept: "User Experience", count: 128 },
      { concept: "Pricing", count: 95 },
      { concept: "Features", count: 87 },
      { concept: "Performance", count: 76 },
    ];
  }

  static generateQuickActions(projects: Project[], insights: Insight[]): QuickAction[] {
    const actions: QuickAction[] = [];

    // Priority 1: Fix Issues
    const blockedProjects = projects.filter((p) => p.status === "blocked");
    blockedProjects.forEach((project) => {
      actions.push({
        id: `fix-${project.id}`,
        title: "Fix Critical Issues",
        description: `${project.name}: ${project.health.blockers[0]}`,
        icon: <AlertCircle className="w-5 h-5" />,
        priority: "critical",
        type: "fix-issues",
        projectId: project.id,
        projectName: project.name,
        action: (onNavigate) => {
          onNavigate?.("projects");
          toast.success("Opening project to fix issues");
        },
      });
    });

    // Priority 2: At-risk projects
    const atRiskProjects = projects.filter((p) => p.health.status === "at-risk");
    atRiskProjects.forEach((project) => {
      if (project.health.blockers.includes("Focus group idle for 52h")) {
        actions.push({
          id: `resume-focus-${project.id}`,
          title: "Resume Focus Group",
          description: `${project.name}: Continue after 52h idle`,
          icon: <Play className="w-5 h-5" />,
          priority: "high",
          type: "start-focus",
          projectId: project.id,
          projectName: project.name,
          action: (onNavigate) => {
            onNavigate?.("focus-groups");
            toast.success("Opening focus groups");
          },
        });
      }
    });

    // Priority 3: View new insights
    const projectsWithNewInsights = projects.filter((p) => p.insights.new > 0);
    if (projectsWithNewInsights.length > 0) {
      const topProject = projectsWithNewInsights.sort((a, b) => b.insights.new - a.insights.new)[0];
      actions.push({
        id: `view-insights-${topProject.id}`,
        title: "Review New Insights",
        description: `${topProject.name}: ${topProject.insights.new} new insights ready`,
        icon: <Lightbulb className="w-5 h-5" />,
        priority: "high",
        type: "view-insights",
        projectId: topProject.id,
        projectName: topProject.name,
        action: (onNavigate) => {
          onNavigate?.("projects");
          toast.success("Opening project insights");
        },
      });
    }

    // Priority 4: Generate personas for low coverage
    const lowCoverageProjects = projects.filter(
      (p) => p.progress.personas < 60 && p.status !== "completed"
    );
    if (lowCoverageProjects.length > 0) {
      const project = lowCoverageProjects[0];
      actions.push({
        id: `gen-personas-${project.id}`,
        title: "Generate Missing Personas",
        description: `${project.name}: Coverage at ${project.progress.personas}%`,
        icon: <Users className="w-5 h-5" />,
        priority: "medium",
        type: "generate-personas",
        projectId: project.id,
        projectName: project.name,
        action: (onNavigate) => {
          onNavigate?.("personas");
          toast.success("Opening personas");
        },
      });
    }

    // Priority 5: Start new research (if no critical issues)
    if (actions.length < 3) {
      actions.push({
        id: "new-research",
        title: "Start New Research Project",
        description: "All systems operational - good time to start new research",
        icon: <Plus className="w-5 h-5" />,
        priority: "low",
        type: "new-research",
        action: (onNavigate) => {
          onNavigate?.("projects");
          toast.success("Opening projects to create new");
        },
      });
    }

    return actions.slice(0, 4); // Max 4 actions
  }
}

// Utility Functions
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

function getHealthColor(status: ProjectHealth["status"]): string {
  switch (status) {
    case "on-track":
      return "bg-green-500";
    case "at-risk":
      return "bg-amber-500";
    case "blocked":
      return "bg-red-500";
  }
}

function getStatusColor(status: Project["status"]): string {
  switch (status) {
    case "running":
      return "bg-green-500";
    case "paused":
      return "bg-amber-500";
    case "completed":
      return "bg-blue-500";
    case "blocked":
      return "bg-red-500";
  }
}

function getPriorityColor(priority: QuickAction["priority"]): string {
  switch (priority) {
    case "critical":
      return "destructive";
    case "high":
      return "default";
    case "medium":
      return "secondary";
    case "low":
      return "outline";
  }
}

// Components
interface DashboardProps {
  onNavigate?: (view: string) => void;
}

export function Dashboard({ onNavigate }: DashboardProps) {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Simulate data loading
  useState(() => {
    setTimeout(() => setLoading(false), 800);
  });

  // Load data
  const kpiMetrics = useMemo(() => DashboardService.getKPIMetrics(), []);
  const projects = useMemo(() => DashboardService.getProjects(), []);
  const insights = useMemo(() => DashboardService.getInsights(), []);
  const notificationData = useMemo(() => DashboardService.getNotifications(), []);
  const usageMetrics = useMemo(() => DashboardService.getUsageMetrics(), []);
  const weeklyTrend = useMemo(() => DashboardService.getWeeklyTrend(), []);
  const insightTypes = useMemo(() => DashboardService.getInsightTypesDistribution(), []);
  const topConcepts = useMemo(() => DashboardService.getTopConcepts(), []);

  const quickActions = useMemo(
    () => DashboardService.generateQuickActions(projects, insights),
    [projects, insights]
  );

  const handleMarkNotificationRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const handleActionClick = useCallback((action: QuickAction) => {
    action.action(onNavigate);
  }, [onNavigate]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="w-full max-w-[1920px] mx-auto space-y-6 px-2 sm:px-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-foreground">Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time insights, actions, and research progress
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => onNavigate?.("settings")}
          >
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
          <Button
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
            onClick={() => onNavigate?.("projects")}
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {/* Overview Cards - 4 main + extensions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Active Research
            </CardTitle>
            <FolderOpen className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {kpiMetrics.activeProjects.running}
            </div>
            <p className="text-xs text-muted-foreground">
              {kpiMetrics.activeProjects.blocked} blocked •{" "}
              {kpiMetrics.activeProjects.paused} paused
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Pending Actions
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {quickActions.filter((a) => a.priority === "critical" || a.priority === "high").length}
            </div>
            <p className="text-xs text-muted-foreground">
              {quickActions.filter((a) => a.priority === "critical").length} critical issues
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Insights Ready
            </CardTitle>
            <Lightbulb className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {projects.reduce((sum, p) => sum + p.insights.new, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {insights.length} total insights this week
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              This Week Activity
            </CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground flex items-center gap-2">
              {kpiMetrics.weeklyActivity.personas}
              <TrendingUp className="w-4 h-4 text-green-600" />
            </div>
            <p className="text-xs text-muted-foreground">
              +{kpiMetrics.weeklyActivity.trend.toFixed(1)}% from last week
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Extended KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Time-to-Insight
            </CardTitle>
            <Clock className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {kpiMetrics.timeToInsight.median}h
            </div>
            <p className="text-xs text-green-600 flex items-center gap-1">
              <TrendingDown className="w-3 h-3" />
              {Math.abs(kpiMetrics.timeToInsight.trend).toFixed(1)}% faster (P90: {kpiMetrics.timeToInsight.p90}h)
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Insight Adoption
            </CardTitle>
            <Target className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {kpiMetrics.insightAdoptionRate.current}%
            </div>
            <Progress value={kpiMetrics.insightAdoptionRate.current} className="h-2 mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Target: {kpiMetrics.insightAdoptionRate.target}%
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Persona Coverage
            </CardTitle>
            <Users className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {kpiMetrics.personaCoverage.current}%
            </div>
            <Progress value={kpiMetrics.personaCoverage.current} className="h-2 mt-2" />
            <p className="text-xs text-amber-600">
              {kpiMetrics.personaCoverage.gapSegments.length} segments missing
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Active Blockers
            </CardTitle>
            <XCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl text-foreground">
              {projects.reduce((sum, p) => sum + p.health.blockers.length, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Most common: Low coverage
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions (Next Best Action) */}
      {quickActions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Zap className="w-5 h-5 text-primary" />
              Quick Actions
            </CardTitle>
            <CardDescription>
              Prioritized actions to maximize research velocity
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {quickActions.map((action) => (
                <div
                  key={action.id}
                  className={`p-4 rounded-lg border-2 ${
                    action.priority === "critical"
                      ? "border-destructive bg-destructive/5"
                      : action.priority === "high"
                      ? "border-primary bg-primary/5"
                      : "border-border bg-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div
                        className={`p-2 rounded-lg ${
                          action.priority === "critical"
                            ? "bg-destructive text-destructive-foreground"
                            : action.priority === "high"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {action.icon}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-foreground mb-1">{action.title}</h4>
                        <p className="text-sm text-muted-foreground">
                          {action.description}
                        </p>
                        {action.projectName && (
                          <Badge variant="outline" className="mt-2">
                            {action.projectName}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      className="bg-primary hover:bg-primary/90 text-primary-foreground"
                      onClick={() => handleActionClick(action)}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Research Projects */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-foreground">Active Research Projects</CardTitle>
              <CardDescription>
                Monitor progress, health, and insights across all projects
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate?.("projects")}
            >
              <Eye className="w-4 h-4 mr-2" />
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {projects.map((project) => (
              <div
                key={project.id}
                className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-foreground">{project.name}</h4>
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(project.status)}`} />
                      <Badge variant="outline" className="capitalize">
                        {project.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {project.lastActivity}
                      <span>•</span>
                      <div className="flex items-center gap-1">
                        <div className={`w-3 h-3 rounded-full ${getHealthColor(project.health.status)}`} />
                        <span className="capitalize">{project.health.status.replace("-", " ")}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {project.status === "running" && (
                      <>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => onNavigate?.("projects")}
                        >
                          <Eye className="w-3 h-3" />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            toast.success(`${project.name} paused`);
                          }}
                        >
                          <Pause className="w-3 h-3" />
                        </Button>
                      </>
                    )}
                    {project.status === "paused" && (
                      <>
                        <Button 
                          size="sm" 
                          className="bg-primary hover:bg-primary/90 text-primary-foreground"
                          onClick={() => {
                            toast.success(`${project.name} resumed`);
                          }}
                        >
                          <Play className="w-3 h-3 mr-1" />
                          Resume
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            toast.success(`${project.name} archived`);
                          }}
                        >
                          <Archive className="w-3 h-3" />
                        </Button>
                      </>
                    )}
                    {project.status === "completed" && (
                      <>
                        <Button 
                          size="sm" 
                          className="bg-primary hover:bg-primary/90 text-primary-foreground"
                          onClick={() => {
                            toast.success("Exporting project data...");
                          }}
                        >
                          <Download className="w-3 h-3 mr-1" />
                          Export
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            toast.success(`${project.name} archived`);
                          }}
                        >
                          <Archive className="w-3 h-3" />
                        </Button>
                      </>
                    )}
                    {project.status === "blocked" && (
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => onNavigate?.("projects")}
                      >
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Fix Issues
                      </Button>
                    )}
                  </div>
                </div>

                {/* Progress bars for stages */}
                <div className="grid grid-cols-4 gap-3 mb-3">
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-muted-foreground">Demographics</span>
                      <span className="text-foreground">{project.progress.demographics}%</span>
                    </div>
                    <Progress value={project.progress.demographics} className="h-1.5" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-muted-foreground">Personas</span>
                      <span className="text-foreground">{project.progress.personas}%</span>
                    </div>
                    <Progress value={project.progress.personas} className="h-1.5" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-muted-foreground">Focus</span>
                      <span className="text-foreground">{project.progress.focus}%</span>
                    </div>
                    <Progress value={project.progress.focus} className="h-1.5" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-muted-foreground">Analysis</span>
                      <span className="text-foreground">{project.progress.analysis}%</span>
                    </div>
                    <Progress value={project.progress.analysis} className="h-1.5" />
                  </div>
                </div>

                {/* Insights & Blockers */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5 text-sm">
                      <Lightbulb className="w-4 h-4 text-primary" />
                      <span className="text-foreground">
                        {project.insights.new > 0 && (
                          <span className="text-primary mr-1">+{project.insights.new}</span>
                        )}
                        {project.insights.total} insights
                      </span>
                    </div>
                  </div>
                  {project.health.blockers.length > 0 && (
                    <div className="text-xs text-destructive flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {project.health.blockers[0]}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Research Activity Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Weekly Completion Trend */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-foreground">Weekly Activity Trend</CardTitle>
            <CardDescription>Personas, focus groups, and insights generation</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={weeklyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="personas"
                  stroke="#F27405"
                  strokeWidth={2}
                  name="Personas"
                />
                <Line
                  type="monotone"
                  dataKey="focusGroups"
                  stroke="#F29F05"
                  strokeWidth={2}
                  name="Focus Groups"
                />
                <Line
                  type="monotone"
                  dataKey="insights"
                  stroke="#28a745"
                  strokeWidth={2}
                  name="Insights"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Concepts */}
        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">Top Insight Concepts</CardTitle>
            <CardDescription>Most frequently discussed topics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={topConcepts} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" stroke="hsl(var(--muted-foreground))" />
                <YAxis dataKey="concept" type="category" stroke="hsl(var(--muted-foreground))" width={120} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="count" fill="#F27405" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Insight Types & Latest Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {/* Insight Types Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-foreground">Insight Types</CardTitle>
            <CardDescription>Distribution by category</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={insightTypes}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {insightTypes.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 mt-4">
              {insightTypes.map((type) => (
                <div key={type.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: type.color }} />
                    <span className="text-card-foreground">{type.name}</span>
                  </div>
                  <span className="text-muted-foreground">{type.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Latest Insights */}
        <Card className="lg:col-span-2 xl:col-span-3">
          <CardHeader>
            <CardTitle className="text-foreground">Latest Insights</CardTitle>
            <CardDescription>High-confidence findings from recent research</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {insights.slice(0, 3).map((insight) => (
                <div
                  key={insight.id}
                  className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-start gap-2 flex-1">
                      <div
                        className={`p-1.5 rounded-lg ${
                          insight.type === "opportunity"
                            ? "bg-green-100 text-green-600"
                            : insight.type === "risk"
                            ? "bg-red-100 text-red-600"
                            : "bg-amber-100 text-amber-600"
                        }`}
                      >
                        {insight.type === "opportunity" ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : insight.type === "risk" ? (
                          <AlertTriangle className="w-4 h-4" />
                        ) : (
                          <Activity className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-foreground">{insight.title}</h4>
                          <Badge
                            variant={
                              insight.impact === "high"
                                ? "default"
                                : insight.impact === "medium"
                                ? "secondary"
                                : "outline"
                            }
                          >
                            {insight.impact} impact
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {insight.description}
                        </p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Shield className="w-3 h-3" />
                            <span>{insight.confidence}% confidence</span>
                          </div>
                          <span>•</span>
                          <span>{formatTimeAgo(insight.timestamp)}</span>
                          <span>•</span>
                          <span>{insight.projectName}</span>
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        onNavigate?.("projects");
                        toast.success("Opening project insights");
                      }}
                    >
                      <Eye className="w-3 h-3 mr-1" />
                      Explore
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Health & Blockers + Usage & Budget */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Health & Blockers */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-foreground flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-destructive" />
              Health & Blockers
            </CardTitle>
            <CardDescription>Active issues requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {projects
                .filter((p) => p.health.blockers.length > 0)
                .map((project) =>
                  project.health.blockers.map((blocker, idx) => (
                    <div
                      key={`${project.id}-${idx}`}
                      className="flex items-start justify-between gap-3 p-3 rounded-lg bg-destructive/5 border border-destructive/20"
                    >
                      <div className="flex items-start gap-2 flex-1">
                        <AlertTriangle className="w-4 h-4 text-destructive mt-0.5" />
                        <div>
                          <h5 className="text-sm text-foreground mb-0.5">
                            {project.name}
                          </h5>
                          <p className="text-sm text-muted-foreground">{blocker}</p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => {
                          onNavigate?.("projects");
                          toast.success("Opening project to fix issue");
                        }}
                      >
                        Fix
                      </Button>
                    </div>
                  ))
                )}
              {projects.filter((p) => p.health.blockers.length > 0).length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-600" />
                  <p>No active blockers - all systems operational</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Usage & Budget */}
        <Card>
          <CardHeader>
            <CardTitle className="text-foreground flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-primary" />
              Usage & Budget
            </CardTitle>
            <CardDescription>Token consumption and cost tracking</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Current Usage</span>
                  <span className="text-foreground">
                    ${usageMetrics.cost.toFixed(2)} / ${usageMetrics.budget.toFixed(2)}
                  </span>
                </div>
                <Progress
                  value={(usageMetrics.cost / usageMetrics.budget) * 100}
                  className="h-2"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {usageMetrics.tokens.toLocaleString()} tokens consumed
                </p>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Forecast (EOM)</p>
                  <p className="text-lg text-foreground">${usageMetrics.forecast.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Alert Threshold</p>
                  <p className="text-lg text-foreground">{usageMetrics.threshold}%</p>
                </div>
              </div>

              {usageMetrics.cost / usageMetrics.budget >= usageMetrics.threshold / 100 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Budget Alert</AlertTitle>
                  <AlertDescription>
                    Usage at {((usageMetrics.cost / usageMetrics.budget) * 100).toFixed(0)}% - consider optimization
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notifications & Tasks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary" />
            Notifications & Tasks
          </CardTitle>
          <CardDescription>Important alerts and actionable items</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {notificationData.slice(0, 5).map((notification) => (
              <div
                key={notification.id}
                className={`flex items-start justify-between gap-3 p-3 rounded-lg border ${
                  notification.read
                    ? "bg-card border-border"
                    : "bg-primary/5 border-primary/20"
                }`}
              >
                <div className="flex items-start gap-2 flex-1">
                  <div
                    className={`p-1.5 rounded-lg ${
                      notification.priority === "high"
                        ? "bg-destructive/10 text-destructive"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <Bell className="w-3 h-3" />
                  </div>
                  <div className="flex-1">
                    <h5 className="text-sm text-foreground mb-0.5">
                      {notification.title}
                    </h5>
                    <p className="text-xs text-muted-foreground">
                      {notification.description}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatTimeAgo(notification.timestamp)}
                    </p>
                  </div>
                </div>
                {notification.actionable && !notification.read && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleMarkNotificationRead(notification.id)}
                  >
                    Mark Done
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Empty State Example - Shown when no projects */}
      {projects.length === 0 && (
        <Card className="border-2 border-dashed">
          <CardContent className="py-12">
            <div className="text-center max-w-md mx-auto">
              <div className="w-16 h-16 mx-auto mb-4 bg-primary/10 rounded-full flex items-center justify-center">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-foreground mb-2">
                Start Your First Research Project
              </h3>
              <p className="text-muted-foreground mb-6">
                Create personas, run focus groups, and extract insights in minutes with AI-powered research
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  onClick={() => onNavigate?.("projects")}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Project
                </Button>
                <Button variant="outline">
                  <Eye className="w-4 h-4 mr-2" />
                  View Demo
                </Button>
              </div>
              <div className="mt-6 flex items-center justify-center gap-4 text-sm text-muted-foreground">
                <a href="#" className="hover:text-primary">Tutorial</a>
                <span>•</span>
                <a href="#" className="hover:text-primary">Documentation</a>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Loading Skeleton
function DashboardSkeleton() {
  return (
    <div className="w-full max-w-[1920px] mx-auto space-y-6 px-2 sm:px-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <Card key={i} className="xl:col-span-2">
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}
