import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger, DialogFooter } from './ui/dialog';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { ScrollArea } from './ui/scroll-area';
import { Progress } from './ui/progress';
import { Plus, Search, Users, MessageSquare, Calendar, FolderOpen, Clock, CheckCircle2, AlertCircle, MoreVertical, TrendingUp } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { toast } from 'sonner@2.0.3';

interface Milestone {
  id: number;
  name: string;
  dueDate: string;
  status: 'completed' | 'in-progress' | 'pending';
  progress: number;
}

interface TimelinePhase {
  name: string;
  startDate: string;
  endDate: string;
  status: 'completed' | 'in-progress' | 'pending';
  progress: number;
}

interface Risk {
  id: number;
  description: string;
  level: 'high' | 'medium' | 'low';
  mitigation: string;
}

interface Project {
  id: number;
  name: string;
  description: string;
  status: string;
  personas: number;
  focusGroups: number;
  createdAt: string;
  completedGroups: number;
  timeline?: {
    phases: TimelinePhase[];
  };
  milestones?: Milestone[];
  risks?: Risk[];
}

const mockProjects: Project[] = [
  {
    id: 1,
    name: 'Product Launch Research',
    description: 'Comprehensive market research for upcoming product launch in Q2 2024.',
    status: 'Active',
    personas: 25,
    focusGroups: 3,
    createdAt: '2024-01-15',
    completedGroups: 2,
    timeline: {
      phases: [
        { name: 'Planning', startDate: '2024-01-15', endDate: '2024-01-30', status: 'completed', progress: 100 },
        { name: 'Data Collection', startDate: '2024-02-01', endDate: '2024-02-28', status: 'in-progress', progress: 65 },
        { name: 'Analysis', startDate: '2024-03-01', endDate: '2024-03-15', status: 'pending', progress: 0 }
      ]
    },
    milestones: [
      { id: 1, name: 'Research Plan Approved', dueDate: '2024-01-25', status: 'completed', progress: 100 },
      { id: 2, name: 'Personas Generated', dueDate: '2024-02-10', status: 'completed', progress: 100 },
      { id: 3, name: 'Focus Groups Completed', dueDate: '2024-02-25', status: 'in-progress', progress: 67 },
      { id: 4, name: 'Final Report', dueDate: '2024-03-15', status: 'pending', progress: 0 }
    ],
    risks: [
      { id: 1, description: 'Low response rate from target demographic', level: 'high', mitigation: 'Increase incentives and extend collection period' },
      { id: 2, description: 'Timeline delays due to holiday season', level: 'medium', mitigation: 'Buffer time built into schedule' }
    ]
  },
  {
    id: 2,
    name: 'Brand Perception Study',
    description: 'Understanding how customers perceive our brand compared to competitors.',
    status: 'Completed',
    personas: 18,
    focusGroups: 2,
    createdAt: '2024-01-10',
    completedGroups: 2,
    timeline: {
      phases: [
        { name: 'Planning', startDate: '2024-01-10', endDate: '2024-01-20', status: 'completed', progress: 100 },
        { name: 'Data Collection', startDate: '2024-01-21', endDate: '2024-02-05', status: 'completed', progress: 100 },
        { name: 'Analysis', startDate: '2024-02-06', endDate: '2024-02-15', status: 'completed', progress: 100 }
      ]
    },
    milestones: [
      { id: 1, name: 'Research Design Finalized', dueDate: '2024-01-18', status: 'completed', progress: 100 },
      { id: 2, name: 'Data Collection Complete', dueDate: '2024-02-05', status: 'completed', progress: 100 },
      { id: 3, name: 'Report Delivered', dueDate: '2024-02-15', status: 'completed', progress: 100 }
    ],
    risks: []
  },
  {
    id: 3,
    name: 'Market Segmentation Analysis',
    description: 'Identifying key market segments for targeted marketing strategies.',
    status: 'In Progress',
    personas: 32,
    focusGroups: 4,
    createdAt: '2024-01-20',
    completedGroups: 1,
    timeline: {
      phases: [
        { name: 'Planning', startDate: '2024-01-20', endDate: '2024-02-01', status: 'completed', progress: 100 },
        { name: 'Data Collection', startDate: '2024-02-02', endDate: '2024-03-10', status: 'in-progress', progress: 40 },
        { name: 'Analysis', startDate: '2024-03-11', endDate: '2024-03-25', status: 'pending', progress: 0 }
      ]
    },
    milestones: [
      { id: 1, name: 'Segmentation Framework', dueDate: '2024-01-28', status: 'completed', progress: 100 },
      { id: 2, name: 'First Wave Data', dueDate: '2024-02-15', status: 'in-progress', progress: 60 },
      { id: 3, name: 'Segment Profiles', dueDate: '2024-03-20', status: 'pending', progress: 0 }
    ],
    risks: [
      { id: 1, description: 'Sample size too small for some segments', level: 'medium', mitigation: 'Oversample in key demographics' },
      { id: 2, description: 'Budget constraints', level: 'low', mitigation: 'Prioritize most valuable segments' }
    ]
  },
  {
    id: 4,
    name: 'Customer Journey Mapping',
    description: 'Mapping the complete customer journey from awareness to purchase.',
    status: 'Planning',
    personas: 0,
    focusGroups: 0,
    createdAt: '2024-01-25',
    completedGroups: 0,
    timeline: {
      phases: [
        { name: 'Planning', startDate: '2024-01-25', endDate: '2024-02-10', status: 'in-progress', progress: 30 },
        { name: 'Data Collection', startDate: '2024-02-11', endDate: '2024-03-05', status: 'pending', progress: 0 },
        { name: 'Analysis', startDate: '2024-03-06', endDate: '2024-03-20', status: 'pending', progress: 0 }
      ]
    },
    milestones: [
      { id: 1, name: 'Journey Framework Defined', dueDate: '2024-02-05', status: 'in-progress', progress: 50 },
      { id: 2, name: 'Touchpoints Mapped', dueDate: '2024-02-28', status: 'pending', progress: 0 },
      { id: 3, name: 'Final Journey Map', dueDate: '2024-03-20', status: 'pending', progress: 0 }
    ],
    risks: [
      { id: 1, description: 'Complex multi-channel journey difficult to map', level: 'high', mitigation: 'Break into phases and prioritize channels' }
    ]
  }
];

interface ProjectsProps {
  onSelectProject: (project: any) => void;
  showCreateDialog?: boolean;
  onCreateDialogChange?: (show: boolean) => void;
}

export function Projects({ onSelectProject, showCreateDialog: externalShowCreateDialog, onCreateDialogChange }: ProjectsProps) {
  const [projects, setProjects] = useState<Project[]>(mockProjects);
  const [searchTerm, setSearchTerm] = useState('');
  const [internalShowCreateDialog, setInternalShowCreateDialog] = useState(false);
  const [showTimelineDialog, setShowTimelineDialog] = useState(false);
  const [showMilestonesDialog, setShowMilestonesDialog] = useState(false);
  const [showRisksDialog, setShowRisksDialog] = useState(false);
  const [selectedProjectForView, setSelectedProjectForView] = useState<Project | null>(null);
  
  // Use external state if provided, otherwise use internal state
  const showCreateDialog = externalShowCreateDialog !== undefined ? externalShowCreateDialog : internalShowCreateDialog;
  const setShowCreateDialog = onCreateDialogChange || setInternalShowCreateDialog;
  const [newProject, setNewProject] = useState({
    name: '',
    description: ''
  });

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateProject = () => {
    if (newProject.name && newProject.description) {
      const project: Project = {
        id: projects.length + 1,
        name: newProject.name,
        description: newProject.description,
        status: 'Planning',
        personas: 0,
        focusGroups: 0,
        createdAt: new Date().toISOString().split('T')[0],
        completedGroups: 0,
        timeline: {
          phases: [
            { name: 'Planning', startDate: new Date().toISOString().split('T')[0], endDate: '', status: 'in-progress', progress: 0 },
            { name: 'Data Collection', startDate: '', endDate: '', status: 'pending', progress: 0 },
            { name: 'Analysis', startDate: '', endDate: '', status: 'pending', progress: 0 }
          ]
        },
        milestones: [],
        risks: []
      };
      setProjects([...projects, project]);
      setNewProject({ name: '', description: '' });
      setShowCreateDialog(false);
      toast.success('Project created successfully');
    }
  };

  const getStatusColor = (status: string) => {
    return 'bg-muted text-muted-foreground border-border';
  };

  const getMilestoneIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    if (status === 'in-progress') return <Clock className="w-4 h-4 text-brand-orange" />;
    return <AlertCircle className="w-4 h-4 text-muted-foreground" />;
  };

  const getRiskColor = (level: string) => {
    if (level === 'high') return 'bg-red-500/10 text-red-600 border-red-500/30';
    if (level === 'medium') return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/30';
    return 'bg-blue-500/10 text-blue-600 border-blue-500/30';
  };

  return (
    <div className="w-full max-w-[1920px] mx-auto space-y-6 px-2 sm:px-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground mb-2">Projects</h1>
          <p className="text-muted-foreground">Manage your market research projects with timelines and milestones</p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-brand-orange hover:bg-brand-orange/90 text-white">
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-popover border border-border text-popover-foreground shadow-xl">
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Create a new market research project to start collecting insights and analyzing data.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Project Name</Label>
                <Input
                  id="name"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="bg-input-background border-border text-foreground"
                  placeholder="Enter project name"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="bg-input-background border-border text-foreground"
                  placeholder="Describe your project objectives"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowCreateDialog(false)}
                  className="border-border text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateProject}
                  className="bg-brand-orange hover:bg-brand-orange/90 text-white shadow-md"
                >
                  Create Project
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 bg-input-background border-border text-foreground shadow-sm"
        />
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProjects.map((project) => (
          <Card 
            key={project.id} 
            className="bg-card border border-border hover:border-ring/50 hover:shadow-lg transition-all group shadow-md"
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1" onClick={() => onSelectProject(project)} className="cursor-pointer">
                  <CardTitle className="text-card-foreground group-hover:text-brand-orange transition-colors">
                    {project.name}
                  </CardTitle>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onSelectProject(project)}>
                      <FolderOpen className="w-4 h-4 mr-2" />
                      View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => {
                      setSelectedProjectForView(project);
                      setShowTimelineDialog(true);
                    }}>
                      <Calendar className="w-4 h-4 mr-2" />
                      View Timeline
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => {
                      setSelectedProjectForView(project);
                      setShowMilestonesDialog(true);
                    }}>
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      View Milestones
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => {
                      setSelectedProjectForView(project);
                      setShowRisksDialog(true);
                    }}>
                      <AlertCircle className="w-4 h-4 mr-2" />
                      View Risks
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <div onClick={() => onSelectProject(project)} className="cursor-pointer">
                <Badge className={getStatusColor(project.status)}>
                  {project.status}
                </Badge>
                <p className="text-muted-foreground text-sm line-clamp-2 mt-2">
                  {project.description}
                </p>
              </div>
            </CardHeader>
            <CardContent onClick={() => onSelectProject(project)} className="cursor-pointer">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-brand-orange" />
                  <span className="text-sm text-card-foreground">{project.personas} personas</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-brand-orange" />
                  <span className="text-sm text-card-foreground">{project.focusGroups} groups</span>
                </div>
              </div>

              {/* Timeline Preview */}
              {project.timeline && (
                <div className="space-y-2 mb-4">
                  <p className="text-xs text-muted-foreground">Timeline Progress:</p>
                  {project.timeline.phases.map((phase, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-foreground">{phase.name}</span>
                        <span className={
                          phase.status === 'completed' ? 'text-green-600' :
                          phase.status === 'in-progress' ? 'text-brand-orange' :
                          'text-muted-foreground'
                        }>
                          {phase.progress}%
                        </span>
                      </div>
                      <Progress value={phase.progress} className="h-1" />
                    </div>
                  ))}
                </div>
              )}

              {/* Milestones Preview */}
              {project.milestones && project.milestones.length > 0 && (
                <div className="pt-2 border-t border-border">
                  <p className="text-xs text-muted-foreground mb-2">Next Milestone:</p>
                  {project.milestones.find(m => m.status !== 'completed') && (
                    <div className="flex items-start gap-2">
                      {getMilestoneIcon(project.milestones.find(m => m.status !== 'completed')!.status)}
                      <div className="flex-1">
                        <p className="text-xs text-foreground">{project.milestones.find(m => m.status !== 'completed')!.name}</p>
                        <p className="text-xs text-muted-foreground">Due: {project.milestones.find(m => m.status !== 'completed')!.dueDate}</p>
                      </div>
                    </div>
                  )}
                  {!project.milestones.find(m => m.status !== 'completed') && (
                    <p className="text-xs text-green-600">All milestones completed!</p>
                  )}
                </div>
              )}
              
              <div className="flex items-center justify-between mt-4 pt-2 border-t border-border">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">
                    {new Date(project.createdAt).toLocaleDateString()}
                  </span>
                </div>
                {project.focusGroups > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {project.completedGroups}/{project.focusGroups} completed
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <div className="text-center py-12">
          <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-foreground mb-2">No projects found</h3>
          <p className="text-muted-foreground mb-4">
            {searchTerm ? 'No projects match your search criteria.' : 'Get started by creating your first project.'}
          </p>
          {!searchTerm && (
            <Button 
              onClick={() => setShowCreateDialog(true)}
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Project
            </Button>
          )}
        </div>
      )}

      {/* Timeline Dialog */}
      <Dialog open={showTimelineDialog} onOpenChange={setShowTimelineDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-brand-orange" />
              Project Timeline - {selectedProjectForView?.name}
            </DialogTitle>
            <DialogDescription>
              Track project phases and progress
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[400px]">
            <div className="space-y-6 p-1">
              {selectedProjectForView?.timeline?.phases.map((phase, index) => (
                <Card key={index} className="bg-card border border-border">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-foreground text-base">{phase.name}</CardTitle>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                          <span>Start: {phase.startDate}</span>
                          {phase.endDate && <span>End: {phase.endDate}</span>}
                        </div>
                      </div>
                      <Badge variant="outline" className={
                        phase.status === 'completed' ? 'bg-green-500/10 text-green-600 border-green-500/30' :
                        phase.status === 'in-progress' ? 'bg-brand-orange/10 text-brand-orange border-brand-orange/30' :
                        'bg-muted text-muted-foreground border-border'
                      }>
                        {phase.status === 'completed' ? 'Completed' :
                         phase.status === 'in-progress' ? 'In Progress' : 'Pending'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="text-foreground">{phase.progress}%</span>
                      </div>
                      <Progress value={phase.progress} className="h-2" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTimelineDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Milestones Dialog */}
      <Dialog open={showMilestonesDialog} onOpenChange={setShowMilestonesDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-brand-orange" />
              Project Milestones - {selectedProjectForView?.name}
            </DialogTitle>
            <DialogDescription>
              Track key deliverables and deadlines
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[400px]">
            <div className="space-y-3 p-1">
              {selectedProjectForView?.milestones?.map((milestone) => (
                <Card key={milestone.id} className="bg-card border border-border">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      {getMilestoneIcon(milestone.status)}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="text-sm text-foreground">{milestone.name}</h4>
                            <p className="text-xs text-muted-foreground">Due: {milestone.dueDate}</p>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {milestone.progress}%
                          </Badge>
                        </div>
                        <Progress value={milestone.progress} className="h-1.5" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {(!selectedProjectForView?.milestones || selectedProjectForView.milestones.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No milestones defined yet
                </p>
              )}
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMilestonesDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Risks Dialog */}
      <Dialog open={showRisksDialog} onOpenChange={setShowRisksDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-brand-orange" />
              Risk Assessment - {selectedProjectForView?.name}
            </DialogTitle>
            <DialogDescription>
              Identified risks and mitigation strategies
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[400px]">
            <div className="space-y-3 p-1">
              {selectedProjectForView?.risks?.map((risk) => (
                <Card key={risk.id} className="bg-card border border-border">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between">
                        <p className="text-sm text-foreground flex-1">{risk.description}</p>
                        <Badge variant="outline" className={getRiskColor(risk.level)}>
                          {risk.level.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="pl-4 border-l-2 border-brand-orange/30">
                        <p className="text-xs text-muted-foreground mb-1">Mitigation:</p>
                        <p className="text-sm text-foreground">{risk.mitigation}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {(!selectedProjectForView?.risks || selectedProjectForView.risks.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No risks identified
                </p>
              )}
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRisksDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
