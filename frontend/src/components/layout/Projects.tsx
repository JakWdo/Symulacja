import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, Search, Users, MessageSquare, Calendar, FolderOpen, MoreVertical, Trash2 } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { projectsApi, personasApi, focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { formatDate } from '@/lib/utils';
import type { Project } from '@/types';
import { Logo } from '@/components/ui/logo';
import { DeleteProjectDialog } from '@/components/projects/DeleteProjectDialog';
import { useTranslation } from 'react-i18next';

interface ProjectsProps {
  onSelectProject?: (project: Project) => void;
}

export function Projects({ onSelectProject }: ProjectsProps = {}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    target_sample_size: 20,
  });
  const { t } = useTranslation('projects');
  const { t: tCommon } = useTranslation('common');

  const { setSelectedProject } = useAppStore();
  const shouldOpenProjectCreation = useAppStore((state) => state.shouldOpenProjectCreation);
  const clearProjectCreationTrigger = useAppStore((state) => state.clearProjectCreationTrigger);
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

  // Handle project creation trigger from dashboard Quick Actions
  useEffect(() => {
    if (shouldOpenProjectCreation) {
      setShowCreateDialog(true);
      clearProjectCreationTrigger();
    }
  }, [shouldOpenProjectCreation, clearProjectCreationTrigger]);

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

    if (projectPersonas.length > 0 && projectFocusGroups.length > 0) {
      return t('panel.projectStatus.active');
    }
    if (projectPersonas.length > 0) {
      return t('panel.projectStatus.inProgress');
    }
    return t('panel.projectStatus.planning');
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
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
      {/* Header */}
      <PageHeader
        title={t('panel.title')}
        subtitle={t('panel.subtitle')}
        actions={
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="bg-brand hover:bg-brand/90 text-brand-foreground">
                <Plus className="w-4 h-4 mr-2" />
                {t('panel.createButton')}
              </Button>
            </DialogTrigger>
          <DialogContent className="bg-popover border border-border text-popover-foreground shadow-xl">
            <DialogHeader>
              <DialogTitle>{t('panel.createForm.title')}</DialogTitle>
              <DialogDescription>
                {t('panel.createForm.description')}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">{t('panel.createForm.nameLabel')}</Label>
                <Input
                  id="name"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="mt-1"
                  placeholder={t('panel.createForm.namePlaceholder')}
                />
              </div>
              <div>
                <Label htmlFor="description">{t('panel.createForm.descriptionLabel')}</Label>
                <Textarea
                  id="description"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="mt-1"
                  placeholder={t('panel.createForm.descriptionPlaceholder')}
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="sample_size">{t('panel.createForm.sampleSizeLabel')}</Label>
                <Input
                  id="sample_size"
                  type="number"
                  value={newProject.target_sample_size}
                  onChange={(e) => setNewProject({ ...newProject, target_sample_size: parseInt(e.target.value) })}
                  className="mt-1"
                  placeholder={t('panel.createForm.sampleSizePlaceholder')}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateDialog(false)}
                  disabled={createMutation.isPending}
                >
                  {tCommon('buttons.cancel')}
                </Button>
                <Button
                  onClick={handleCreateProject}
                  disabled={createMutation.isPending || !newProject.name || !newProject.description}
                >
                  {createMutation.isPending && <Logo className="w-4 h-4 mr-2" spinning />}
                  {t('panel.createForm.createButton')}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
        }
      />

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          placeholder={t('panel.searchPlaceholder')}
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
              className="bg-card border border-border hover:border-primary/50 hover:shadow-lg transition-all group shadow-md"
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => {
                      setSelectedProject(project);
                      if (onSelectProject) {
                        onSelectProject(project);
                      }
                    }}
                  >
                    <CardTitle className="text-card-foreground group-hover:text-primary transition-colors">
                      {project.name}
                    </CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(project)}>
                      {getStatusLabel(project)}
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreVertical className="h-4 w-4" />
                          <span className="sr-only">{t('accessibility.openMenu')}</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        className="text-destructive focus:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          setProjectToDelete(project);
                          setShowDeleteDialog(true);
                        }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        {t('panel.actions.deleteProject')}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
                <p
                  className="text-muted-foreground text-sm line-clamp-2 cursor-pointer"
                  onClick={() => {
                    setSelectedProject(project);
                    if (onSelectProject) {
                      onSelectProject(project);
                    }
                  }}
                >
                  {project.description || t('panel.noDescription')}
                </p>
              </CardHeader>
              <CardContent
                className="cursor-pointer"
                onClick={() => {
                  setSelectedProject(project);
                  if (onSelectProject) {
                    onSelectProject(project);
                  }
                }}
              >
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-chart-4" />
                    <span className="text-sm text-card-foreground">
                      {t('panel.projectStats.personas', {
                        count: allPersonas.filter(p => p.project_id === project.id).length,
                      })}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-chart-1" />
                    <span className="text-sm text-card-foreground">
                      {t('panel.projectStats.focusGroups', {
                        count: allFocusGroups.filter(fg => fg.project_id === project.id).length,
                      })}
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
                    {t('panel.goalLabel', { count: project.target_sample_size })}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">
            {t('panel.emptyState.title')}
          </h3>
          <p className="text-muted-foreground mb-4">
            {searchTerm
              ? t('panel.emptyState.searchDescription')
              : t('panel.emptyState.defaultDescription')}
          </p>
          {!searchTerm && (
            <Button
              onClick={() => setShowCreateDialog(true)}
              className="bg-brand hover:bg-brand/90 text-brand-foreground"
            >
              <Plus className="w-4 h-4 mr-2" />
              {t('panel.emptyState.primaryAction')}
            </Button>
          )}
        </div>
      )}

      {/* Delete Project Dialog */}
      <DeleteProjectDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        project={projectToDelete}
        onSuccess={() => {
          setProjectToDelete(null);
        }}
      />
      </div>
    </div>
  );
}
