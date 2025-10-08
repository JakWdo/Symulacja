import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Search, Users, MessageSquare, Calendar, FolderOpen } from 'lucide-react';
import { projectsApi, personasApi, focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { formatDate } from '@/lib/utils';
import type { Project } from '@/types';
import { Logo } from '@/components/ui/Logo';

interface ProjectsProps {
  onSelectProject?: (project: Project) => void;
}

export function Projects({ onSelectProject }: ProjectsProps = {}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    target_sample_size: 20,
  });
  
  const { setSelectedProject } = useAppStore();
  const queryClient = useQueryClient();

  // Fetch projects
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  // Create project mutation
  const createMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setNewProject({ name: '', description: '', target_sample_size: 20 });
      setShowCreateDialog(false);
      setSelectedProject(newProject);
    },
  });

  const filteredProjects = projects.filter((project: Project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (project.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
  );

  const handleCreateProject = () => {
    if (newProject.name && newProject.description) {
      createMutation.mutate({
        name: newProject.name,
        description: newProject.description,
        target_demographics: {
          age_group: { '18-24': 0.3, '25-34': 0.4, '35-44': 0.3 },
          gender: { Male: 0.5, Female: 0.5 },
        },
        target_sample_size: newProject.target_sample_size,
      });
    }
  };

  const getStatusColor = () => {
    return 'bg-muted text-muted-foreground border-border';
  };

  const getStatusLabel = (project: Project) => {
    const projectPersonas = allPersonas.filter(p => p.project_id === project.id);
    const projectFocusGroups = allFocusGroups.filter(fg => fg.project_id === project.id);

    if (projectPersonas.length > 0 && projectFocusGroups.length > 0) return 'Active';
    if (projectPersonas.length > 0) return 'In Progress';
    return 'Planning';
  };

  // Fetch all personas and focus groups for project cards
  const { data: allPersonas = [] } = useQuery({
    queryKey: ['personas', 'all'],
    queryFn: async () => {
      if (projects.length === 0) return [];
      const personaArrays = await Promise.all(
        projects.map(p => personasApi.getByProject(p.id).catch(() => []))
      );
      return personaArrays.flat();
    },
    enabled: projects.length > 0,
  });

  const { data: allFocusGroups = [] } = useQuery({
    queryKey: ['focusGroups', 'all'],
    queryFn: async () => {
      if (projects.length === 0) return [];
      const fgArrays = await Promise.all(
        projects.map(p => focusGroupsApi.getByProject(p.id).catch(() => []))
      );
      return fgArrays.flat();
    },
    enabled: projects.length > 0,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Logo className="w-8 h-8" spinning />
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Projects</h1>
          <p className="text-muted-foreground">Manage your market research projects</p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-[#F27405] hover:bg-[#F27405]/90 text-white">
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
                  className="mt-1"
                  placeholder="Enter project name"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="mt-1"
                  placeholder="Describe your project objectives"
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="sample_size">Target Sample Size</Label>
                <Input
                  id="sample_size"
                  type="number"
                  value={newProject.target_sample_size}
                  onChange={(e) => setNewProject({ ...newProject, target_sample_size: parseInt(e.target.value) })}
                  className="mt-1"
                  placeholder="20"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowCreateDialog(false)}
                  disabled={createMutation.isPending}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleCreateProject}
                  disabled={createMutation.isPending || !newProject.name || !newProject.description}
                >
                  {createMutation.isPending && <Logo className="w-4 h-4 mr-2" spinning />}
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
          className="pl-10"
        />
      </div>

      {/* Projects Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project: Project) => (
            <Card
              key={project.id}
              className="bg-card border border-border hover:border-primary/50 hover:shadow-lg transition-all cursor-pointer group shadow-md"
              onClick={() => {
                setSelectedProject(project);
                if (onSelectProject) {
                  onSelectProject(project);
                }
              }}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-card-foreground group-hover:text-primary transition-colors">
                    {project.name}
                  </CardTitle>
                  <Badge className={getStatusColor(project)}>
                    {getStatusLabel(project)}
                  </Badge>
                </div>
                <p className="text-muted-foreground text-sm line-clamp-2">
                  {project.description || 'No description'}
                </p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-chart-4" />
                    <span className="text-sm text-card-foreground">
                      {allPersonas.filter(p => p.project_id === project.id).length} personas
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-chart-1" />
                    <span className="text-sm text-card-foreground">
                      {allFocusGroups.filter(fg => fg.project_id === project.id).length} groups
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {formatDate(project.created_at)}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Target: {project.target_sample_size}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No projects found</h3>
          <p className="text-muted-foreground mb-4">
            {searchTerm ? 'No projects match your search criteria.' : 'Get started by creating your first project.'}
          </p>
          {!searchTerm && (
            <Button
              onClick={() => setShowCreateDialog(true)}
              className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Project
            </Button>
          )}
        </div>
      )}
      </div>
    </div>
  );
}
