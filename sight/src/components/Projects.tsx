import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Plus, Search, Users, MessageSquare, Calendar, FolderOpen } from 'lucide-react';

const mockProjects = [
  {
    id: 1,
    name: 'Product Launch Research',
    description: 'Comprehensive market research for upcoming product launch in Q2 2024.',
    status: 'Active',
    personas: 25,
    focusGroups: 3,
    createdAt: '2024-01-15',
    completedGroups: 2
  },
  {
    id: 2,
    name: 'Brand Perception Study',
    description: 'Understanding how customers perceive our brand compared to competitors.',
    status: 'Completed',
    personas: 18,
    focusGroups: 2,
    createdAt: '2024-01-10',
    completedGroups: 2
  },
  {
    id: 3,
    name: 'Market Segmentation Analysis',
    description: 'Identifying key market segments for targeted marketing strategies.',
    status: 'In Progress',
    personas: 32,
    focusGroups: 4,
    createdAt: '2024-01-20',
    completedGroups: 1
  },
  {
    id: 4,
    name: 'Customer Journey Mapping',
    description: 'Mapping the complete customer journey from awareness to purchase.',
    status: 'Planning',
    personas: 0,
    focusGroups: 0,
    createdAt: '2024-01-25',
    completedGroups: 0
  }
];

interface ProjectsProps {
  onSelectProject: (project: any) => void;
  showCreateDialog?: boolean;
  onCreateDialogChange?: (show: boolean) => void;
}

export function Projects({ onSelectProject, showCreateDialog: externalShowCreateDialog, onCreateDialogChange }: ProjectsProps) {
  const [projects, setProjects] = useState(mockProjects);
  const [searchTerm, setSearchTerm] = useState('');
  const [internalShowCreateDialog, setInternalShowCreateDialog] = useState(false);
  
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
      const project = {
        id: projects.length + 1,
        name: newProject.name,
        description: newProject.description,
        status: 'Planning',
        personas: 0,
        focusGroups: 0,
        createdAt: new Date().toISOString().split('T')[0],
        completedGroups: 0
      };
      setProjects([...projects, project]);
      setNewProject({ name: '', description: '' });
      setShowCreateDialog(false);
    }
  };

  const getStatusColor = (status: string) => {
    return 'bg-muted text-muted-foreground border-border';
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Projects</h1>
          <p className="text-muted-foreground">Manage your market research projects</p>
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
            className="bg-card border border-border hover:border-ring/50 hover:shadow-lg transition-all cursor-pointer group shadow-md"
            onClick={() => onSelectProject(project)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-card-foreground group-hover:text-chart-1 transition-colors">
                  {project.name}
                </CardTitle>
                <Badge className={getStatusColor(project.status)}>
                  {project.status}
                </Badge>
              </div>
              <p className="text-muted-foreground text-sm line-clamp-2">
                {project.description}
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-chart-4" />
                  <span className="text-sm text-card-foreground">{project.personas} personas</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-chart-1" />
                  <span className="text-sm text-card-foreground">{project.focusGroups} groups</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
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
          <h3 className="text-lg font-medium text-foreground mb-2">No projects found</h3>
          <p className="text-muted-foreground mb-4">
            {searchTerm ? 'No projects match your search criteria.' : 'Get started by creating your first project.'}
          </p>
          {!searchTerm && (
            <Button 
              onClick={() => setShowCreateDialog(true)}
              className="bg-gradient-to-r from-chart-1 to-chart-4 hover:opacity-90 shadow-md"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Project
            </Button>
          )}
        </div>
      )}
    </div>
  );
}