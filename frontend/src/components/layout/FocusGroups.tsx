import { useQuery } from '@tanstack/react-query';
import { useAppStore } from '@/store/appStore';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MoreVertical, Plus, Users, MessageSquare, Eye, Settings, Loader2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { focusGroupsApi } from '@/lib/api';

interface FocusGroupsProps {
  onCreateFocusGroup: () => void;
  onSelectFocusGroup: (focusGroup: any) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

export function FocusGroups({ onCreateFocusGroup, onSelectFocusGroup }: FocusGroupsProps) {
  const { selectedProject } = useAppStore();

  const { data: focusGroups = [], isLoading } = useQuery({
    queryKey: ['focus-groups', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return await focusGroupsApi.getByProject(selectedProject.id);
    },
    enabled: !!selectedProject,
  });

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Please select a project to view focus groups</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Focus Groups</h1>
          <p className="text-muted-foreground">
            Conduct in-depth qualitative research with AI-powered focus group sessions
          </p>
        </div>
        <Button
          onClick={onCreateFocusGroup}
          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Focus Group
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-[400px]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : focusGroups.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[400px] space-y-4">
          <MessageSquare className="w-16 h-16 text-muted-foreground" />
          <h2 className="text-2xl font-bold text-foreground">No Focus Groups Yet</h2>
          <p className="text-muted-foreground">Create your first focus group to get started.</p>
          <Button
            className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
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
                        <div className="mb-2">
                          <h3 className="text-lg font-semibold text-card-foreground">{focusGroup.name}</h3>
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
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Progress and Details */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Participants</span>
                          <span className="text-card-foreground">
                            {focusGroup.persona_ids?.length || 0} / {focusGroup.persona_ids?.length || 0}
                          </span>
                        </div>
                        <Progress value={100} className="h-2" />
                        <p className="text-xs text-muted-foreground">100% Full</p>
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
                            : focusGroup.status === 'pending'
                            ? 'Ready to start'
                            : 'Failed'
                          }
                        </p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {focusGroup.status === 'completed' && (
                        <Button
                          size="sm"
                          onClick={() => onSelectFocusGroup(focusGroup)}
                          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View Results
                        </Button>
                      )}
                      {focusGroup.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onSelectFocusGroup(focusGroup)}
                          className="border-border text-muted-foreground hover:text-foreground"
                        >
                          <Settings className="w-4 h-4 mr-2" />
                          Setup Focus Group
                        </Button>
                      )}
                      {focusGroup.status === 'running' && (
                        <Button
                          size="sm"
                          onClick={() => onSelectFocusGroup(focusGroup)}
                          className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                        >
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          In Progress
                        </Button>
                      )}
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
  );
}