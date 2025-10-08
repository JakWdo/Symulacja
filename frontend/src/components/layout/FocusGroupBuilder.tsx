import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Plus, Trash2, Users, MessageSquare, Settings, Check } from 'lucide-react';
import { projectsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { SpinnerLogo } from '@/components/ui/SpinnerLogo';

interface FocusGroupBuilderProps {
  onBack: () => void;
  onSave: (focusGroup: any) => void;
}

export function FocusGroupBuilder({ onBack, onSave }: FocusGroupBuilderProps) {
  const { data: projects = [], isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });
  const { selectedProject: globalProject } = useAppStore();
  const [focusGroupTitle, setFocusGroupTitle] = useState('');
  const [focusGroupDescription, setFocusGroupDescription] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [participantCount, setParticipantCount] = useState('8');
  const [discussionTopics, setDiscussionTopics] = useState<string[]>(['']);
  const [researchQuestions, setResearchQuestions] = useState<string[]>(['']);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (globalProject && selectedProject === '') {
      setSelectedProject(globalProject.id);
    } else if (!globalProject && projects.length > 0 && selectedProject === '') {
      setSelectedProject(projects[0].id);
    }
  }, [globalProject, projects, selectedProject]);

  const addDiscussionTopic = () => {
    setDiscussionTopics([...discussionTopics, '']);
  };

  const updateDiscussionTopic = (index: number, value: string) => {
    const newTopics = [...discussionTopics];
    newTopics[index] = value;
    setDiscussionTopics(newTopics);
  };

  const removeDiscussionTopic = (index: number) => {
    if (discussionTopics.length > 1) {
      setDiscussionTopics(discussionTopics.filter((_, i) => i !== index));
    }
  };

  const addResearchQuestion = () => {
    setResearchQuestions([...researchQuestions, '']);
  };

  const updateResearchQuestion = (index: number, value: string) => {
    const newQuestions = [...researchQuestions];
    newQuestions[index] = value;
    setResearchQuestions(newQuestions);
  };

  const removeResearchQuestion = (index: number) => {
    if (researchQuestions.length > 1) {
      setResearchQuestions(researchQuestions.filter((_, i) => i !== index));
    }
  };

  const handleCreate = async () => {
    setIsSaving(true);
    try {
      const focusGroup = {
        title: focusGroupTitle,
        description: focusGroupDescription,
        projectId: selectedProject,
        targetParticipants: parseInt(participantCount),
        discussionTopics: discussionTopics.filter(topic => topic.trim() !== ''),
        researchQuestions: researchQuestions.filter(question => question.trim() !== ''),
      };
      await onSave(focusGroup);
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Focus Groups
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl brand-orange">Focus Group Builder</h1>
          <p className="text-muted-foreground">Set up a new focus group session</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleCreate}
            disabled={!focusGroupTitle || !selectedProject || isSaving}
            className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
          >
            {isSaving ? (
              <SpinnerLogo className="w-4 h-4 mr-2" />
            ) : (
              <Check className="w-4 h-4 mr-2" />
            )}
            Create Focus Group
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-card-foreground">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Focus Group Title</Label>
                <Input
                  id="title"
                  value={focusGroupTitle}
                  onChange={(e) => setFocusGroupTitle(e.target.value)}
                  placeholder="e.g., Mobile App Usability Testing"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={focusGroupDescription}
                  onChange={(e) => setFocusGroupDescription(e.target.value)}
                  placeholder="Brief description of the focus group objectives and scope"
                  rows={3}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="project">Associated Project</Label>
                <Select value={selectedProject} onValueChange={setSelectedProject}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                <SelectContent>
                  {projectsLoading ? (
                    <div className="flex items-center justify-center p-2">
                      <SpinnerLogo className="w-4 h-4" />
                    </div>
                  ) : (
                    projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            </CardContent>
          </Card>

          {/* Session Configuration */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-card-foreground">Session Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="participants">Target Participants</Label>
                <Select value={participantCount} onValueChange={setParticipantCount}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="4">4 participants</SelectItem>
                    <SelectItem value="6">6 participants</SelectItem>
                    <SelectItem value="8">8 participants</SelectItem>
                    <SelectItem value="10">10 participants</SelectItem>
                    <SelectItem value="12">12 participants</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Discussion Topics */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-card-foreground flex items-center justify-between">
                Discussion Topics
                <Badge variant="outline">
                  {discussionTopics.filter(topic => topic.trim() !== '').length} topic{discussionTopics.filter(topic => topic.trim() !== '').length !== 1 ? 's' : ''}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {discussionTopics.map((topic, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="flex-1">
                    <Input
                      value={topic}
                      onChange={(e) => updateDiscussionTopic(index, e.target.value)}
                      placeholder={`Discussion topic ${index + 1}`}
                    />
                  </div>
                  {discussionTopics.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeDiscussionTopic(index)}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="ghost"
                size="sm"
                onClick={addDiscussionTopic}
                className="text-primary hover:text-primary"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Topic
              </Button>
            </CardContent>
          </Card>

          {/* Research Questions */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-card-foreground flex items-center justify-between">
                Key Research Questions
                <Badge variant="outline">
                  {researchQuestions.filter(q => q.trim() !== '').length} question{researchQuestions.filter(q => q.trim() !== '').length !== 1 ? 's' : ''}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {researchQuestions.map((question, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className="flex-1">
                    <Textarea
                      value={question}
                      onChange={(e) => updateResearchQuestion(index, e.target.value)}
                      placeholder={`Research question ${index + 1}`}
                      rows={2}
                    />
                  </div>
                  {researchQuestions.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeResearchQuestion(index)}
                      className="text-destructive hover:text-destructive mt-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="ghost"
                size="sm"
                onClick={addResearchQuestion}
                className="text-primary hover:text-primary"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Question
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Configuration Summary */}
        <div className="lg:col-span-1">
          <Card className="bg-card border border-border sticky top-6">
            <CardHeader>
              <CardTitle className="text-card-foreground flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Configuration Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                  <Users className="w-5 h-5 brand-orange" />
                  <div>
                    <p className="text-sm text-card-foreground">Participants</p>
                    <p className="text-xs text-muted-foreground">{participantCount} people</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                  <MessageSquare className="w-5 h-5 brand-orange" />
                  <div>
                    <p className="text-sm text-card-foreground">Topics</p>
                    <p className="text-xs text-muted-foreground">
                      {discussionTopics.filter(topic => topic.trim() !== '').length} discussion areas
                    </p>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2 text-xs text-muted-foreground">
                <p>AI personas will be automatically generated based on your project demographics</p>
                <p>The AI moderator will guide the discussion and ask follow-up questions</p>
                <p>Results will be analyzed for themes, sentiment, and key insights</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  </div>
  );
}
