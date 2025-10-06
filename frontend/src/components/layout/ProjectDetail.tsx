import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Users, MessageSquare, Settings as SettingsIcon, Plus, Loader2, Eye } from 'lucide-react';
import { PersonaGenerationWizard } from '@/components/personas/PersonaGenerationWizard';
import { personasApi, focusGroupsApi, projectsApi, type GeneratePersonasPayload, type CreateFocusGroupPayload } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';
import type { Project, Persona, FocusGroup } from '@/types';

interface ProjectDetailProps {
  project: Project;
  onBack: () => void;
  onSelectFocusGroup: (focusGroup: FocusGroup) => void;
}

export function ProjectDetail({ project, onBack, onSelectFocusGroup }: ProjectDetailProps) {
  const [showPersonaWizard, setShowPersonaWizard] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [showCreateFocusGroup, setShowCreateFocusGroup] = useState(false);
  const [newFocusGroup, setNewFocusGroup] = useState({
    name: '',
    description: '',
    questions: ['']
  });
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([]);

  const { setSelectedProject } = useAppStore();

  // Fetch personas for this project
  const { data: personas = [], isLoading: personasLoading, refetch: refetchPersonas } = useQuery({
    queryKey: ['personas', project.id],
    queryFn: () => personasApi.getByProject(project.id),
  });

  // Fetch focus groups for this project
  const { data: focusGroups = [], isLoading: focusGroupsLoading, refetch: refetchFocusGroups } = useQuery({
    queryKey: ['focus-groups', project.id],
    queryFn: () => focusGroupsApi.getByProject(project.id),
  });

  const handleGeneratePersonas = async (config: GeneratePersonasPayload) => {
    try {
      await personasApi.generate(project.id, config);
      setShowPersonaWizard(false);
      // Refetch will happen automatically via polling
      setTimeout(() => refetchPersonas(), 2000);
    } catch (error) {
      console.error('Failed to generate personas:', error);
    }
  };

  const handleCreateFocusGroup = async () => {
    if (!newFocusGroup.name || selectedPersonaIds.length < 2) return;

    const payload: CreateFocusGroupPayload = {
      name: newFocusGroup.name,
      description: newFocusGroup.description || null,
      persona_ids: selectedPersonaIds,
      questions: newFocusGroup.questions.filter(q => q.trim()),
      mode: 'normal'
    };

    try {
      await focusGroupsApi.create(project.id, payload);
      setNewFocusGroup({ name: '', description: '', questions: [''] });
      setSelectedPersonaIds([]);
      setShowCreateFocusGroup(false);
      refetchFocusGroups();
    } catch (error) {
      console.error('Failed to create focus group:', error);
    }
  };

  const addQuestion = () => {
    setNewFocusGroup({
      ...newFocusGroup,
      questions: [...newFocusGroup.questions, '']
    });
  };

  const updateQuestion = (index: number, value: string) => {
    const updated = [...newFocusGroup.questions];
    updated[index] = value;
    setNewFocusGroup({ ...newFocusGroup, questions: updated });
  };

  const removeQuestion = (index: number) => {
    setNewFocusGroup({
      ...newFocusGroup,
      questions: newFocusGroup.questions.filter((_, i) => i !== index)
    });
  };

  const togglePersonaSelection = (personaId: string) => {
    setSelectedPersonaIds(prev =>
      prev.includes(personaId)
        ? prev.filter(id => id !== personaId)
        : [...prev, personaId]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-chart-1/10 text-chart-1 border-chart-1/20';
      case 'running':
        return 'bg-chart-2/10 text-chart-2 border-chart-2/20';
      case 'pending':
        return 'bg-muted text-muted-foreground border-border';
      case 'failed':
        return 'bg-destructive/10 text-destructive border-destructive/20';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Projects
        </Button>
        <div>
          <h1 className="text-3xl font-semibold text-foreground">{project.name}</h1>
          <p className="text-muted-foreground">{project.description}</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="setup" className="w-full">
        <TabsList className="bg-muted border border-border">
          <TabsTrigger value="setup" className="data-[state=active]:bg-background data-[state=active]:text-foreground">
            <SettingsIcon className="w-4 h-4 mr-2" />
            Setup
          </TabsTrigger>
          <TabsTrigger value="personas" className="data-[state=active]:bg-background data-[state=active]:text-foreground">
            <Users className="w-4 h-4 mr-2" />
            Personas ({personas.length})
          </TabsTrigger>
          <TabsTrigger value="focus-groups" className="data-[state=active]:bg-background data-[state=active]:text-foreground">
            <MessageSquare className="w-4 h-4 mr-2" />
            Focus Groups ({focusGroups.length})
          </TabsTrigger>
        </TabsList>

        {/* Setup Tab */}
        <TabsContent value="setup" className="space-y-6">
          <Card className="bg-card border border-border shadow-md">
            <CardHeader>
              <CardTitle className="text-foreground">Project Configuration</CardTitle>
              <p className="text-muted-foreground">Configure your project settings and target demographics</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="project-name">Project Name</Label>
                  <Input
                    id="project-name"
                    defaultValue={project.name}
                    className="bg-input-background border-border text-foreground"
                    disabled
                  />
                </div>
                <div>
                  <Label htmlFor="target-size">Target Sample Size</Label>
                  <Input
                    id="target-size"
                    defaultValue={project.target_sample_size}
                    className="bg-input-background border-border text-foreground"
                    disabled
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="project-description">Description</Label>
                <Textarea
                  id="project-description"
                  defaultValue={project.description || ''}
                  className="bg-input-background border-border text-foreground"
                  rows={3}
                  disabled
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Personas Tab */}
        <TabsContent value="personas" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-foreground">Generated Personas</h2>
              <p className="text-muted-foreground">AI-generated user personas based on your demographics</p>
            </div>

            <Button
              className="bg-gradient-to-r from-chart-1 to-chart-4 hover:opacity-90 bg-primary"
              onClick={() => setShowPersonaWizard(true)}
            >
              <Plus className="w-4 h-4 mr-2" />
              Generate Personas
            </Button>
          </div>

          {personasLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : personas.length === 0 ? (
            <Card className="bg-card border border-border">
              <CardContent className="text-center py-12">
                <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No personas yet</h3>
                <p className="text-muted-foreground mb-4">
                  Generate your first cohort to start building focus groups
                </p>
                <Button onClick={() => setShowPersonaWizard(true)} className="bg-primary">
                  <Plus className="w-4 h-4 mr-2" />
                  Generate Personas
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {personas.map((persona) => (
                <Card key={persona.id} className="bg-card border border-border hover:border-primary/50 hover:shadow-lg transition-all">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-foreground text-lg">{persona.full_name || `Person ${persona.age}`}</CardTitle>
                        <p className="text-sm text-muted-foreground">{persona.age} years old</p>
                        <p className="text-sm text-muted-foreground">{persona.occupation || 'No occupation'}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedPersona(persona)}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {persona.interests && persona.interests.length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Interests</p>
                          <div className="flex flex-wrap gap-1">
                            {persona.interests.slice(0, 3).map((interest, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs bg-muted text-muted-foreground">
                                {interest}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {persona.background_story && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Background</p>
                          <p className="text-xs text-foreground line-clamp-2">{persona.background_story}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Persona Detail Dialog */}
          <Dialog open={!!selectedPersona} onOpenChange={() => setSelectedPersona(null)}>
            <DialogContent className="bg-background border border-border text-foreground max-w-2xl">
              {selectedPersona && (
                <>
                  <DialogHeader>
                    <DialogTitle className="text-xl">{selectedPersona.full_name || `Person ${selectedPersona.age}`}</DialogTitle>
                    <DialogDescription>
                      Detailed view of this persona's characteristics, demographics, and behavioral patterns.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm text-muted-foreground">Age</Label>
                        <p className="text-foreground">{selectedPersona.age} years old</p>
                      </div>
                      <div>
                        <Label className="text-sm text-muted-foreground">Gender</Label>
                        <p className="text-foreground">{selectedPersona.gender || 'Not specified'}</p>
                      </div>
                      <div>
                        <Label className="text-sm text-muted-foreground">Occupation</Label>
                        <p className="text-foreground">{selectedPersona.occupation || 'Not specified'}</p>
                      </div>
                      <div>
                        <Label className="text-sm text-muted-foreground">Location</Label>
                        <p className="text-foreground">{selectedPersona.location || 'Not specified'}</p>
                      </div>
                    </div>

                    {selectedPersona.interests && selectedPersona.interests.length > 0 && (
                      <div>
                        <Label className="text-sm text-muted-foreground">Interests</Label>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {selectedPersona.interests.map((interest, idx) => (
                            <Badge key={idx} variant="secondary" className="bg-muted text-muted-foreground">
                              {interest}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedPersona.background_story && (
                      <div>
                        <Label className="text-sm text-muted-foreground">Background</Label>
                        <p className="text-foreground mt-1">{selectedPersona.background_story}</p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </DialogContent>
          </Dialog>

          {/* Persona Generation Wizard */}
          <PersonaGenerationWizard
            open={showPersonaWizard}
            onOpenChange={setShowPersonaWizard}
            onGenerate={(config) => {
              handleGeneratePersonas({
                num_personas: config.personaCount,
                adversarial_mode: config.adversarialMode,
              });
            }}
          />
        </TabsContent>

        {/* Focus Groups Tab */}
        <TabsContent value="focus-groups" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-foreground">Focus Groups</h2>
              <p className="text-muted-foreground">Manage and create focus group sessions</p>
            </div>

            <Dialog open={showCreateFocusGroup} onOpenChange={setShowCreateFocusGroup}>
              <DialogTrigger asChild>
                <Button className="bg-primary hover:bg-primary/90" disabled={personas.length < 2}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Focus Group
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-background border border-border text-foreground max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Focus Group</DialogTitle>
                  <DialogDescription>
                    Set up a new focus group session with selected personas to gather insights and feedback.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="focus-group-name">Group Name</Label>
                    <Input
                      id="focus-group-name"
                      value={newFocusGroup.name}
                      onChange={(e) => setNewFocusGroup({ ...newFocusGroup, name: e.target.value })}
                      className="bg-input-background border-border text-foreground"
                      placeholder="Enter focus group name"
                    />
                  </div>

                  <div>
                    <Label htmlFor="focus-group-description">Description (optional)</Label>
                    <Textarea
                      id="focus-group-description"
                      value={newFocusGroup.description}
                      onChange={(e) => setNewFocusGroup({ ...newFocusGroup, description: e.target.value })}
                      className="bg-input-background border-border text-foreground"
                      placeholder="Describe the purpose of this focus group"
                      rows={2}
                    />
                  </div>

                  <div>
                    <Label>Discussion Questions</Label>
                    <div className="space-y-2 mt-2">
                      {newFocusGroup.questions.map((question, index) => (
                        <div key={index} className="flex gap-2">
                          <Input
                            value={question}
                            onChange={(e) => updateQuestion(index, e.target.value)}
                            className="bg-input-background border-border text-foreground flex-1"
                            placeholder={`Question ${index + 1}`}
                          />
                          {newFocusGroup.questions.length > 1 && (
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => removeQuestion(index)}
                              className="border-border"
                            >
                              Remove
                            </Button>
                          )}
                        </div>
                      ))}
                      <Button
                        type="button"
                        variant="outline"
                        onClick={addQuestion}
                        className="w-full border-border"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Question
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label>Select Participants (min. 2)</Label>
                    <div className="mt-2 max-h-48 overflow-y-auto border border-border rounded-lg p-2 space-y-2">
                      {personas.map((persona) => (
                        <label
                          key={persona.id}
                          className={cn(
                            'flex items-center gap-2 p-2 rounded cursor-pointer transition-all',
                            selectedPersonaIds.includes(persona.id)
                              ? 'bg-primary/10 border border-primary'
                              : 'bg-muted/30 hover:bg-muted/50'
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={selectedPersonaIds.includes(persona.id)}
                            onChange={() => togglePersonaSelection(persona.id)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm flex-1">{persona.full_name || `Person ${persona.age}`}</span>
                        </label>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Selected: {selectedPersonaIds.length} / {personas.length}
                    </p>
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setShowCreateFocusGroup(false)}
                      className="border-border"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateFocusGroup}
                      className="bg-primary hover:bg-primary/90"
                      disabled={!newFocusGroup.name || selectedPersonaIds.length < 2}
                    >
                      Create Group
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {focusGroupsLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : focusGroups.length === 0 ? (
            <Card className="bg-card border border-border">
              <CardContent className="text-center py-12">
                <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No focus groups yet</h3>
                <p className="text-muted-foreground mb-4">
                  {personas.length >= 2
                    ? 'Create your first focus group to start gathering insights'
                    : 'Generate at least 2 personas first'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {focusGroups.map((group) => (
                <Card
                  key={group.id}
                  className="bg-card border border-border hover:border-primary/50 transition-colors cursor-pointer group shadow-md hover:shadow-lg"
                  onClick={() => onSelectFocusGroup(group)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-foreground group-hover:text-primary transition-colors">
                        {group.name}
                      </CardTitle>
                      <Badge className={getStatusColor(group.status)}>
                        {group.status}
                      </Badge>
                    </div>
                    {group.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {group.description}
                      </p>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">
                        {group.questions.length} questions • {group.persona_ids.length} participants
                      </p>
                      <div className="text-xs text-muted-foreground">
                        Created: {formatDate(group.created_at)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
