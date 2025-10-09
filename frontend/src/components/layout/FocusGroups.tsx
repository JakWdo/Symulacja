import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Plus, Users, MessageSquare, Eye, Settings, Trash2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { focusGroupsApi, projectsApi } from '@/lib/api';
import { SpinnerLogo } from '@/components/ui/SpinnerLogo';
import { toast } from '@/components/ui/toastStore';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useState } from 'react';

interface FocusGroupsProps {
  onCreateFocusGroup: () => void;
  onSelectFocusGroup: (focusGroup: any) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

const getStatusBadge = (focusGroup: any) => {
  switch (focusGroup.status) {
    case 'completed':
      return <Badge className="bg-[#F27405]/10 text-[#F27405] dark:text-[#F27405]">Completed</Badge>;
    case 'running':
      return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">In Progress</Badge>;
    case 'failed':
      return (
        <Badge className="bg-red-100 text-red-700 dark:bg-red-400/10 dark:text-red-400">
          Failed
        </Badge>
      );
    case 'pending':
      if ((focusGroup.persona_ids?.length || 0) === 0 || (focusGroup.questions?.length || 0) === 0) {
        return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">Draft</Badge>;
      }
      return <Badge className="bg-gray-500/10 text-gray-700 dark:text-gray-400">Ready to start</Badge>;
    default:
      return null;
  }
};

export function FocusGroups({ onCreateFocusGroup, onSelectFocusGroup }: FocusGroupsProps) {
  const { selectedProject, setSelectedProject } = useAppStore();
  const queryClient = useQueryClient();
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; focusGroup: any | null }>({
    open: false,
    focusGroup: null,
  });

  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  const { data: focusGroups = [], isLoading } = useQuery({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await focusGroupsApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
    refetchInterval: (query) => {
      // Poll every 2s if any focus group is running
      const data = query.state.data;
      const hasRunningFG = data?.some((fg: any) => fg.status === 'running');
      return hasRunningFG ? 2000 : false;
    },
  });

  const { mutateAsync: deleteFocusGroup, isPending: isDeleting } = useMutation({
    mutationFn: (focusGroupId: string) => focusGroupsApi.remove(focusGroupId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['focus-groups', selectedProject?.id] });
      toast.success('Session archived', 'Your focus group discussion has been removed from the workspace.');
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to delete focus group', message);
    },
  });

  const handleDelete = (focusGroup: any) => {
    if (isDeleting) return;
    setDeleteDialog({ open: true, focusGroup });
  };

  const confirmDelete = async () => {
    if (deleteDialog.focusGroup) {
      await deleteFocusGroup(deleteDialog.focusGroup.id);
      setDeleteDialog({ open: false, focusGroup: null });
    }
  };

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Focus Groups</h1>
          <p className="text-muted-foreground">
            Conduct in-depth qualitative research with AI-powered focus group sessions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={selectedProject?.id || ''}
            onValueChange={(value) => {
              const project = projects.find((p) => p.id === value);
              if (project) setSelectedProject(project);
            }}
          >
            <SelectTrigger className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-0 rounded-md px-3.5 py-2 h-9 hover:bg-[#f0f1f2] dark:hover:bg-[#333333] transition-colors w-56">
              <SelectValue
                placeholder="Select project"
                className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] leading-5"
              />
            </SelectTrigger>
            <SelectContent className="bg-[#f8f9fa] dark:bg-[#2a2a2a] border-border">
              {projectsLoading ? (
                <div className="flex items-center justify-center p-2">
                  <SpinnerLogo className="w-4 h-4" />
                </div>
              ) : projects.length === 0 ? (
                <div className="p-2 text-sm text-muted-foreground">No projects found</div>
              ) : (
                projects.map((project) => (
                  <SelectItem
                    key={project.id}
                    value={project.id}
                    className="font-['Crimson_Text',_serif] text-[14px] text-[#333333] dark:text-[#e5e5e5] focus:bg-[#e9ecef] dark:focus:bg-[#333333]"
                  >
                    {project.name}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
          <Button
            onClick={onCreateFocusGroup}
            className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
            disabled={!selectedProject}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Focus Group
          </Button>
        </div>
      </div>

      {!selectedProject ? (
        <Card className="bg-card border border-border">
          <CardContent className="py-12 text-center space-y-4">
            <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto" />
            <h3 className="text-lg text-card-foreground">No project selected</h3>
            <p className="text-sm text-muted-foreground">
              Choose a project from the dropdown to view and manage focus groups.
            </p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="flex items-center justify-center h-[400px]">
          <SpinnerLogo className="w-10 h-10" />
        </div>
      ) : focusGroups.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[400px] space-y-3">
          <MessageSquare className="w-12 h-12 text-muted-foreground" />
          <h2 className="text-lg font-medium text-foreground">No focus groups yet</h2>
          <p className="text-sm text-muted-foreground">Create your first focus group to conduct qualitative research</p>
          <Button
            className="bg-[#F27405] hover:bg-[#F27405]/90 text-white mt-2"
            onClick={onCreateFocusGroup}
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Focus Group
          </Button>
        </div>
      ) : (
        <>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-card border border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Groups</p>
                    <p className="text-2xl brand-orange">{focusGroups.length}</p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Participants</p>
                    <p className="text-2xl brand-orange">
                      {focusGroups.reduce((sum, fg) => sum + (fg.persona_ids?.length || 0), 0)}
                    </p>
                  </div>
                  <Users className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Focus Groups List */}
          <div className="space-y-4">
            <h2 className="text-xl text-foreground">Your Focus Groups</h2>

            <div className="grid grid-cols-1 gap-4">
              {focusGroups.map((focusGroup) => (
            <Card key={focusGroup.id} className="bg-card border border-border hover:shadow-md transition-shadow shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-card-foreground">{focusGroup.name}</h3>
                          {getStatusBadge(focusGroup)}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {focusGroup.description || 'No description'}
                        </p>
                        <p className="text-xs text-muted-foreground mb-2">
                          {focusGroup.questions?.length || 0} questions • {focusGroup.persona_ids?.length || 0} participants
                        </p>
                      </div>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={() => onSelectFocusGroup(focusGroup)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDelete(focusGroup)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Progress and Details */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Participants</span>
                          <span className="text-card-foreground">
                            {focusGroup.persona_ids?.length || 0} / {focusGroup.target_participants || 10}
                          </span>
                        </div>
                        <Progress
                          value={focusGroup.target_participants ? Math.min((focusGroup.persona_ids?.length || 0) / focusGroup.target_participants * 100, 100) : 0}
                          className="h-2"
                        />
                        <p className="text-xs text-muted-foreground">
                          {focusGroup.target_participants
                            ? `${Math.round(Math.min((focusGroup.persona_ids?.length || 0) / focusGroup.target_participants * 100, 100))}%`
                            : '0%'}
                        </p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Discussion Topics</p>
                        <div className="flex flex-wrap gap-1">
                          {focusGroup.questions?.slice(0, 2).map((question, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              Q{index + 1}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Status</p>
                        <p className="text-xs text-card-foreground">
                          {focusGroup.status === 'completed'
                            ? 'Completed'
                            : focusGroup.status === 'running'
                            ? `In progress (${focusGroup.persona_ids?.length || 0} participants)`
                            : focusGroup.status === 'pending' && (focusGroup.persona_ids?.length === 0 || focusGroup.questions?.length === 0)
                            ? 'Draft'
                            : focusGroup.status === 'pending'
                            ? 'Ready to start'
                            : 'Failed'
                          }
                        </p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      <Button
                        size="sm"
                        onClick={() => onSelectFocusGroup(focusGroup)}
                        className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                      >
                        <Settings className="w-4 h-4 mr-2" />
                        Manage Session
                      </Button>
                      <p className="text-xs text-muted-foreground ml-auto">
                        Created {new Date(focusGroup.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
              ))}
            </div>
          </div>
        </>
      )}
      </div>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, focusGroup: null })}
        title={`Remove "${deleteDialog.focusGroup?.name}"?`}
        description={`This will permanently delete all discussion data and cannot be reversed.`}
        confirmText="Remove Session"
        cancelText="Keep It"
        onConfirm={confirmDelete}
      />
    </div>
  );
}
