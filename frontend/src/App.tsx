import { useState, useEffect, lazy, Suspense } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { ProjectPanel } from '@/components/panels/ProjectPanel';
import { PersonaPanel } from '@/components/panels/PersonaPanel';
import { FocusGroupPanel } from '@/components/panels/FocusGroupPanel';
import { AnalysisPanel } from '@/components/panels/AnalysisPanel';
import { RAGManagementPanel } from '@/components/panels/RAGManagementPanel';
import { AssistantButton } from '@/components/assistant/AssistantButton';
import { ToastContainer } from '@/components/ui/toast';
import { AppLoader } from '@/components/AppLoader';
import { Login } from '@/components/auth/Login';
import { useAuth } from '@/contexts/AuthContext';
import { useAppStore } from '@/store/appStore';
import { personasApi, focusGroupsApi } from '@/lib/api';
import { useTheme } from '@/hooks/use-theme';
import type { Project, FocusGroup, Survey, Workflow } from '@/types';

// Lazy load głównych komponentów widoków dla lepszej wydajności
const OverviewDashboard = lazy(() => import('@/components/layout/OverviewDashboard').then(m => ({ default: m.OverviewDashboard })));
const MainDashboard = lazy(() => import('@/components/layout/MainDashboard').then(m => ({ default: m.MainDashboard })));
const Projects = lazy(() => import('@/components/layout/Projects').then(m => ({ default: m.Projects })));
const ProjectDetail = lazy(() => import('@/components/layout/ProjectDetail').then(m => ({ default: m.ProjectDetail })));
const FocusGroups = lazy(() => import('@/components/layout/FocusGroups').then(m => ({ default: m.FocusGroups })));
const FocusGroupBuilder = lazy(() => import('@/components/layout/FocusGroupBuilder').then(m => ({ default: m.FocusGroupBuilder })));
const FocusGroupView = lazy(() => import('@/components/layout/FocusGroupView').then(m => ({ default: m.FocusGroupView })));
const Personas = lazy(() => import('@/components/layout/Personas').then(m => ({ default: m.Personas })));
const Surveys = lazy(() => import('@/components/layout/Surveys').then(m => ({ default: m.Surveys })));
const SurveyBuilder = lazy(() => import('@/components/layout/SurveyBuilder').then(m => ({ default: m.SurveyBuilder })));
const SurveyResults = lazy(() => import('@/components/layout/SurveyResults').then(m => ({ default: m.SurveyResults })));
const Settings = lazy(() => import('@/components/Settings').then(m => ({ default: m.Settings })));
const WorkflowEditor = lazy(() => import('@/components/workflows/WorkflowEditor').then(m => ({ default: m.WorkflowEditor })));
const WorkflowsListPage = lazy(() => import('@/components/workflows/WorkflowsListPage').then(m => ({ default: m.WorkflowsListPage })));
const TeamsList = lazy(() => import('@/components/teams/TeamsList').then(m => ({ default: m.TeamsList })));
const TeamDetailView = lazy(() => import('@/components/teams/TeamDetailView').then(m => ({ default: m.TeamDetailView })));
const EnvironmentsList = lazy(() => import('@/components/environments/EnvironmentsList').then(m => ({ default: m.EnvironmentsList })));

export default function App() {
  // Initialize theme
  useTheme();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // Use Zustand selectors to prevent unnecessary re-renders
  const selectedProject = useAppStore(state => state.selectedProject);
  const setPersonas = useAppStore(state => state.setPersonas);
  const setSelectedPersona = useAppStore(state => state.setSelectedPersona);

  const [currentView, setCurrentView] = useState('dashboard');
  const [viewProject, setViewProject] = useState<Project | null>(null);
  const [viewFocusGroup, setViewFocusGroup] = useState<FocusGroup | null>(null);
  const [viewSurvey, setViewSurvey] = useState<Survey | null>(null);
  const [viewWorkflow, setViewWorkflow] = useState<Workflow | null>(null);
  const [viewTeam, setViewTeam] = useState<string | null>(null);

  // Fetch personas for selected project
  const { data: personas } = useQuery({
    queryKey: ['personas', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await personasApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
  });

  // Sync fetched personas with the global store
  useEffect(() => {
    if (!selectedProject) {
      setPersonas([]);
      setSelectedPersona(null);
    } else if (personas) {
      setPersonas(personas);
    }
  }, [selectedProject, personas]);

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <MainDashboard
            onNavigate={setCurrentView}
          />
        );
      case 'projects':
        return (
          <Projects
            onSelectProject={(project) => {
              setViewProject(project);
              setCurrentView('project-detail');
            }}
          />
        );
      case 'project-detail':
        return viewProject ? (
          <ProjectDetail
            project={viewProject}
            onBack={() => setCurrentView('projects')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No project selected</p>
          </div>
        );
      case 'focus-groups':
        return (
          <FocusGroups
            onCreateFocusGroup={() => setCurrentView('focus-group-builder')}
            onSelectFocusGroup={(focusGroup) => {
              setViewFocusGroup(focusGroup);
              setCurrentView('focus-group-detail');
            }}
            showCreateDialog={false}
            onCreateDialogChange={() => {}}
          />
        );
      case 'focus-group-builder':
        return (
          <FocusGroupBuilder
            onBack={() => setCurrentView('focus-groups')}
            onSave={async (focusGroupData) => {
              try {
                if (!selectedProject) return;

                // Konwertuj dane z buildera do formatu API
                const payload = {
                  name: focusGroupData.title,
                  description: focusGroupData.description || null,
                  persona_ids: [], // Builder nie wybiera person - musimy to obsłużyć w FocusGroupView
                  questions: focusGroupData.researchQuestions || [],
                  mode: 'normal' as const,
                  target_participants: focusGroupData.targetParticipants || 10,
                };

                const createdFocusGroup = await focusGroupsApi.create(selectedProject.id, payload);

                await queryClient.invalidateQueries({ queryKey: ['focus-groups'] });
                queryClient.setQueryData(['focus-group', createdFocusGroup.id], createdFocusGroup);

                setViewFocusGroup(createdFocusGroup);
                setCurrentView('focus-group-detail');
                return createdFocusGroup;
              } catch (error) {
                console.error('Failed to create focus group:', error);
                toast.error(t('focusGroups:create.error'));
                throw error;
              }
            }}
          />
        );
      case 'focus-group-detail':
        return viewFocusGroup ? (
          <FocusGroupView
            focusGroup={viewFocusGroup}
            onBack={() => setCurrentView('focus-groups')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No focus group selected</p>
          </div>
        );
      case 'personas':
        return <Personas />;
      case 'surveys':
        return (
          <Surveys
            onCreateSurvey={() => setCurrentView('survey-builder')}
            onSelectSurvey={(survey) => {
              setViewSurvey(survey);
              setCurrentView('survey-results');
            }}
          />
        );
      case 'survey-builder':
        return (
          <SurveyBuilder
            onBack={() => setCurrentView('surveys')}
            onSave={() => setCurrentView('surveys')}
          />
        );
      case 'survey-results':
        return viewSurvey ? (
          <SurveyResults
            survey={viewSurvey}
            onBack={() => setCurrentView('surveys')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No survey selected</p>
          </div>
        );
      case 'settings':
        return (
          <div className="h-full overflow-y-auto">
            <div className="mx-auto p-4 sm:p-6 lg:p-8">
              <Settings />
            </div>
          </div>
        );
      case 'workflows':
        return (
          <WorkflowsListPage
            projectId={selectedProject?.id}
            onSelectWorkflow={(workflow) => {
              setViewWorkflow(workflow);
              setCurrentView('workflow-editor');
            }}
          />
        );
      case 'workflow-editor':
        return viewWorkflow ? (
          <WorkflowEditor
            workflowId={viewWorkflow.id}
            onBack={() => setCurrentView('workflows')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No workflow selected</p>
          </div>
        );
      case 'teams':
        return (
          <TeamsList
            onSelectTeam={(team) => {
              setViewTeam(team.id);
              setCurrentView('team-detail');
            }}
          />
        );
      case 'team-detail':
        return viewTeam ? (
          <TeamDetailView
            teamId={viewTeam}
            onBack={() => setCurrentView('teams')}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">No team selected</p>
          </div>
        );
      case 'environments':
        return (
          <EnvironmentsList
            onSelectEnvironment={(env) => {
              // Możesz dodać widok szczegółów environment w przyszłości
              // setCurrentView('environment-detail');
              console.log('Selected environment:', env);
            }}
          />
        );
      default:
        return <OverviewDashboard onNavigate={setCurrentView} />;
    }
  };

  // Show loading screen while checking auth
  if (authLoading) {
    return <AppLoader message="Loading your workspace..." />;
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  // Show main app if authenticated
  return (
    <div className="h-screen bg-background text-foreground">
      <SidebarProvider className="h-full">
        <div className="flex w-full h-full min-h-0">
          <AppSidebar currentView={currentView} onNavigate={setCurrentView} />
          <main className="flex flex-1 min-h-0 bg-background overflow-y-auto">
            <div className="flex-1 min-h-0 h-full">
              <Suspense fallback={<AppLoader message="Loading page..." />}>
                {renderContent()}
              </Suspense>
            </div>
          </main>
        </div>
      </SidebarProvider>

      {/* Preserve existing panels for workflows */}
      <ToastContainer />
      <ProjectPanel />
      <PersonaPanel />
      <FocusGroupPanel />
      <AnalysisPanel />
      <RAGManagementPanel />

      {/* Product Assistant - Floating button w prawym dolnym rogu */}
      <AssistantButton />
    </div>
  );
}
