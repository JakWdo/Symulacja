import { useState, useEffect } from 'react';
import { SidebarProvider } from './components/ui/sidebar';
import { AppSidebar } from './components/AppSidebar';
import { Dashboard } from './components/Dashboard';
import { Projects } from './components/Projects';
import { ProjectDetail } from './components/ProjectDetail';
import { FocusGroup } from './components/FocusGroup';
import { FocusGroups } from './components/FocusGroups';
import { FocusGroupBuilder } from './components/FocusGroupBuilder';
import { Settings } from './components/Settings';
import { Surveys } from './components/Surveys';
import { SurveyBuilder } from './components/SurveyBuilder';
import { SurveyResults } from './components/SurveyResults';
import { Personas } from './components/Personas';
import { GraphAnalysis } from './components/GraphAnalysis';
import { useTheme } from './components/ui/use-theme';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedFocusGroup, setSelectedFocusGroup] = useState(null);
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showCreateSurveyDialog, setShowCreateSurveyDialog] = useState(false);
  const [showCreateFocusGroupDialog, setShowCreateFocusGroupDialog] = useState(false);
  
  // Initialize theme
  useTheme();



  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentView} />;
      case 'projects':
        return <Projects 
          onSelectProject={(project) => {
            setSelectedProject(project);
            setCurrentView('project-detail');
          }}
          showCreateDialog={showCreateDialog}
          onCreateDialogChange={setShowCreateDialog}
        />;
      case 'project-detail':
        return <ProjectDetail 
          project={selectedProject} 
          onBack={() => setCurrentView('projects')}
          onNavigate={setCurrentView}
        />;
      case 'focus-groups':
        return <FocusGroups 
          onCreateFocusGroup={() => setCurrentView('focus-group-builder')}
          onSelectFocusGroup={(focusGroup) => {
            setSelectedFocusGroup(focusGroup);
            setCurrentView('focus-group-detail');
          }}
          showCreateDialog={showCreateFocusGroupDialog}
          onCreateDialogChange={setShowCreateFocusGroupDialog}
        />;
      case 'focus-group-builder':
        return <FocusGroupBuilder 
          onBack={() => setCurrentView('focus-groups')}
          onSave={(focusGroup) => {
            // Handle focus group save
            setCurrentView('focus-groups');
          }}
        />;
      case 'focus-group-detail':
        return <FocusGroup 
          focusGroup={selectedFocusGroup}
          onBack={() => setCurrentView('focus-groups')}
        />;
      case 'surveys':
        return <Surveys 
          onCreateSurvey={() => setCurrentView('survey-builder')}
          onSelectSurvey={(survey) => {
            setSelectedSurvey(survey);
            setCurrentView('survey-results');
          }}
          showCreateDialog={showCreateSurveyDialog}
          onCreateDialogChange={setShowCreateSurveyDialog}
        />;
      case 'survey-builder':
        return <SurveyBuilder 
          onBack={() => setCurrentView('surveys')}
          onSave={(survey) => {
            // Handle survey save
            setCurrentView('surveys');
          }}
        />;
      case 'survey-results':
        return <SurveyResults 
          survey={selectedSurvey}
          onBack={() => setCurrentView('surveys')}
        />;
      case 'personas':
        return <Personas />;
      case 'graph-analysis':
        return <GraphAnalysis />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SidebarProvider>
        <div className="flex w-full">
          <AppSidebar 
            currentView={currentView} 
            onNavigate={setCurrentView}
          />
          <main className="flex-1 p-6 bg-muted/30">
            {renderContent()}
          </main>
        </div>
      </SidebarProvider>
    </div>
  );
}