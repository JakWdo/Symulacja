import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Switch } from './ui/switch';
import { Slider } from './ui/slider';
import { ArrowLeft, Plus, Trash2, Calendar, Users, MessageSquare, Settings, Brain, BarChart3, Zap, Lightbulb, Clock, Target } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface FocusGroupBuilderProps {
  onBack: () => void;
  onSave: (focusGroup: any) => void;
}

const mockProjects = [
  { id: 1, name: "Mobile App Launch Research" },
  { id: 2, name: "Product Development Study" },
  { id: 3, name: "Marketing Research" }
];

export function FocusGroupBuilder({ onBack, onSave }: FocusGroupBuilderProps) {
  const [focusGroupTitle, setFocusGroupTitle] = useState('');
  const [focusGroupDescription, setFocusGroupDescription] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [participantCount, setParticipantCount] = useState('8');
  const [sessionDuration, setSessionDuration] = useState('60');
  const [discussionTopics, setDiscussionTopics] = useState<string[]>(['']);
  const [researchQuestions, setResearchQuestions] = useState<string[]>(['']);
  
  // AI Moderator Settings
  const [aiModeratorEnabled, setAiModeratorEnabled] = useState(true);
  const [moderationStyle, setModerationStyle] = useState('balanced');
  const [probeDepth, setProbeDepth] = useState([5]);
  const [autoFollowUp, setAutoFollowUp] = useState(true);
  
  // Interactive Tools
  const [wordCloudEnabled, setWordCloudEnabled] = useState(true);
  const [livePollEnabled, setLivePollEnabled] = useState(true);
  const [sentimentTrackingEnabled, setSentimentTrackingEnabled] = useState(true);
  const [themeExtractionEnabled, setThemeExtractionEnabled] = useState(true);

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

  const handleSave = () => {
    if (!focusGroupTitle || !selectedProject) {
      toast.error('Please fill in required fields');
      return;
    }

    const focusGroup = {
      title: focusGroupTitle,
      description: focusGroupDescription,
      projectId: selectedProject,
      targetParticipants: parseInt(participantCount),
      sessionDuration: parseInt(sessionDuration),
      discussionTopics: discussionTopics.filter(topic => topic.trim() !== ''),
      researchQuestions: researchQuestions.filter(question => question.trim() !== ''),
      aiModerator: {
        enabled: aiModeratorEnabled,
        style: moderationStyle,
        probeDepth: probeDepth[0],
        autoFollowUp: autoFollowUp
      },
      interactiveTools: {
        wordCloud: wordCloudEnabled,
        livePoll: livePollEnabled,
        sentimentTracking: sentimentTrackingEnabled,
        themeExtraction: themeExtractionEnabled
      },
      status: 'draft'
    };
    onSave(focusGroup);
    toast.success('Focus group created successfully!');
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Focus Groups
        </Button>
        <div className="flex-1">
          <h1 className="text-foreground mb-2">Focus Group Builder</h1>
          <p className="text-muted-foreground">Set up a new AI-moderated focus group session</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleSave} disabled={!focusGroupTitle || !selectedProject}>
            Save Draft
          </Button>
          <Button 
            onClick={handleSave}
            disabled={!focusGroupTitle || !selectedProject}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Create Session
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Sidebar - Configuration */}
        <div className="col-span-4 space-y-4">
          {/* AI Moderator Settings */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-foreground text-sm flex items-center gap-2">
                  <Brain className="w-4 h-4 text-brand-orange" />
                  AI Moderator
                </CardTitle>
                <Switch checked={aiModeratorEnabled} onCheckedChange={setAiModeratorEnabled} />
              </div>
            </CardHeader>
            {aiModeratorEnabled && (
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-xs">Moderation Style</Label>
                  <Select value={moderationStyle} onValueChange={setModerationStyle}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="structured">Structured - Follow script closely</SelectItem>
                      <SelectItem value="balanced">Balanced - Mix of structure & flow</SelectItem>
                      <SelectItem value="exploratory">Exploratory - Follow participant leads</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-xs">Probe Depth</Label>
                    <Badge variant="outline" className="text-xs">{probeDepth[0]}/10</Badge>
                  </div>
                  <Slider 
                    value={probeDepth} 
                    onValueChange={setProbeDepth}
                    min={1}
                    max={10}
                    step={1}
                    className="py-2"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    How deeply AI should probe into responses
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-xs">Auto Follow-up</Label>
                    <p className="text-xs text-muted-foreground">Ask clarifying questions</p>
                  </div>
                  <Switch checked={autoFollowUp} onCheckedChange={setAutoFollowUp} />
                </div>

                <Separator />

                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">AI will:</p>
                  <ul className="text-xs text-foreground space-y-1">
                    <li className="flex items-start gap-2">
                      <span className="text-brand-orange">•</span>
                      <span>Guide discussion flow naturally</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-brand-orange">•</span>
                      <span>Ensure all participants engage</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-brand-orange">•</span>
                      <span>Probe interesting insights</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-brand-orange">•</span>
                      <span>Keep discussion on track</span>
                    </li>
                  </ul>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Interactive Tools */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm flex items-center gap-2">
                <Zap className="w-4 h-4 text-brand-gold" />
                Interactive Tools
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-brand-orange" />
                  <div>
                    <Label className="text-xs">Word Cloud</Label>
                    <p className="text-xs text-muted-foreground">Live keyword visualization</p>
                  </div>
                </div>
                <Switch checked={wordCloudEnabled} onCheckedChange={setWordCloudEnabled} />
              </div>

              <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-brand-orange" />
                  <div>
                    <Label className="text-xs">Live Polling</Label>
                    <p className="text-xs text-muted-foreground">Real-time quick votes</p>
                  </div>
                </div>
                <Switch checked={livePollEnabled} onCheckedChange={setLivePollEnabled} />
              </div>

              <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-brand-orange" />
                  <div>
                    <Label className="text-xs">Sentiment Tracking</Label>
                    <p className="text-xs text-muted-foreground">Track emotional tone</p>
                  </div>
                </div>
                <Switch checked={sentimentTrackingEnabled} onCheckedChange={setSentimentTrackingEnabled} />
              </div>

              <div className="flex items-center justify-between p-3 border border-border rounded-lg">
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-brand-orange" />
                  <div>
                    <Label className="text-xs">Theme Extraction</Label>
                    <p className="text-xs text-muted-foreground">Auto-identify themes</p>
                  </div>
                </div>
                <Switch checked={themeExtractionEnabled} onCheckedChange={setThemeExtractionEnabled} />
              </div>
            </CardContent>
          </Card>

          {/* Session Settings */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm">Session Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-xs">Participants</Label>
                <Input
                  type="number"
                  value={participantCount}
                  onChange={(e) => setParticipantCount(e.target.value)}
                  placeholder="8"
                  min="4"
                  max="12"
                />
                <p className="text-xs text-muted-foreground mt-1">Recommended: 6-10 people</p>
              </div>
              <div>
                <Label className="text-xs flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  Duration (minutes)
                </Label>
                <Input
                  type="number"
                  value={sessionDuration}
                  onChange={(e) => setSessionDuration(e.target.value)}
                  placeholder="60"
                  min="30"
                  max="120"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="col-span-8 space-y-6">
          {/* Basic Details */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground">Session Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Session Title</Label>
                <Input
                  value={focusGroupTitle}
                  onChange={(e) => setFocusGroupTitle(e.target.value)}
                  placeholder="e.g., Product Feature Discovery Session"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={focusGroupDescription}
                  onChange={(e) => setFocusGroupDescription(e.target.value)}
                  placeholder="Brief description of the focus group objectives and goals"
                  rows={3}
                />
              </div>
              <div>
                <Label>Project</Label>
                <Select value={selectedProject} onValueChange={setSelectedProject}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {mockProjects.map((project) => (
                      <SelectItem key={project.id} value={project.id.toString()}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Discussion Topics */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-foreground">Discussion Topics</CardTitle>
                <Button onClick={addDiscussionTopic} size="sm" variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Topic
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {discussionTopics.map((topic, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs min-w-[60px] justify-center">
                    Topic {index + 1}
                  </Badge>
                  <Input
                    value={topic}
                    onChange={(e) => updateDiscussionTopic(index, e.target.value)}
                    placeholder="Enter discussion topic..."
                  />
                  {discussionTopics.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeDiscussionTopic(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <p className="text-xs text-muted-foreground">
                AI moderator will guide the conversation through these topics
              </p>
            </CardContent>
          </Card>

          {/* Research Questions */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-foreground">Research Questions</CardTitle>
                <Button onClick={addResearchQuestion} size="sm" variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Question
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {researchQuestions.map((question, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-start gap-2">
                    <Badge variant="outline" className="text-xs mt-2 min-w-[50px] justify-center">
                      Q{index + 1}
                    </Badge>
                    <Textarea
                      value={question}
                      onChange={(e) => updateResearchQuestion(index, e.target.value)}
                      placeholder="What specific insights do you want to gain?"
                      rows={2}
                    />
                    {researchQuestions.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeResearchQuestion(index)}
                        className="mt-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
              <p className="text-xs text-muted-foreground">
                These questions will guide the AI moderator's probing strategy
              </p>
            </CardContent>
          </Card>

          {/* Preview */}
          <Card className="bg-muted/50 border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm">Session Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Participants</p>
                  <p className="text-sm text-foreground">{participantCount} AI personas</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Duration</p>
                  <p className="text-sm text-foreground">{sessionDuration} minutes</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Topics</p>
                  <p className="text-sm text-foreground">{discussionTopics.filter(t => t.trim()).length} discussion topics</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Questions</p>
                  <p className="text-sm text-foreground">{researchQuestions.filter(q => q.trim()).length} research questions</p>
                </div>
              </div>
              
              <Separator />
              
              <div>
                <p className="text-xs text-muted-foreground mb-2">Active Features</p>
                <div className="flex flex-wrap gap-2">
                  {aiModeratorEnabled && (
                    <Badge variant="outline" className="text-xs">
                      <Brain className="w-3 h-3 mr-1" />
                      AI Moderator ({moderationStyle})
                    </Badge>
                  )}
                  {wordCloudEnabled && (
                    <Badge variant="outline" className="text-xs">Word Cloud</Badge>
                  )}
                  {livePollEnabled && (
                    <Badge variant="outline" className="text-xs">Live Polling</Badge>
                  )}
                  {sentimentTrackingEnabled && (
                    <Badge variant="outline" className="text-xs">Sentiment Tracking</Badge>
                  )}
                  {themeExtractionEnabled && (
                    <Badge variant="outline" className="text-xs">Theme Extraction</Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
