import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { Slider } from './ui/slider';
import { MoreVertical, Plus, Users, MessageSquare, Eye, Settings, Copy, Trash2, Play, Pause, Brain, BarChart2, Palette, ThumbsUp, MessageCircle, Pencil, Share2, Target, Award, Smile, Frown, Meh } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { toast } from 'sonner@2.0.3';

interface FocusGroupsProps {
  onCreateFocusGroup: () => void;
  onSelectFocusGroup: (focusGroup: any) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

interface FocusGroup {
  id: number;
  title: string;
  description: string;
  status: string;
  participants: number;
  targetParticipants: number;
  duration: string;
  createdAt: string;
  completedAt?: string;
  scheduledFor?: string;
  moderator: string;
  topics: string[];
  insights?: {
    satisfaction: string;
    keyFinding: string;
    sentiment?: {
      positive: number;
      neutral: number;
      negative: number;
    };
  };
  sessions: number;
  interactiveTools?: {
    livePolling: boolean;
    whiteboard: boolean;
    reactions: boolean;
    screenShare: boolean;
    cardSorting: boolean;
    voting: boolean;
  };
  aiModerator?: {
    personality: string;
    followUpDepth: number;
    probingEnabled: boolean;
  };
}

const mockFocusGroups: FocusGroup[] = [
  {
    id: 1,
    title: "Mobile App UX Testing",
    description: "User experience evaluation for the new mobile app interface",
    status: "completed",
    participants: 8,
    targetParticipants: 8,
    duration: "90 minutes",
    createdAt: "2024-01-12",
    completedAt: "2024-01-12",
    moderator: "AI Moderator Sarah",
    topics: ["Navigation", "Visual Design", "User Flow"],
    insights: {
      satisfaction: "4.2/5",
      keyFinding: "Navigation needs simplification",
      sentiment: {
        positive: 65,
        neutral: 25,
        negative: 10
      }
    },
    sessions: 1,
    interactiveTools: {
      livePolling: true,
      whiteboard: true,
      reactions: true,
      screenShare: false,
      cardSorting: false,
      voting: true
    },
    aiModerator: {
      personality: "professional",
      followUpDepth: 7,
      probingEnabled: true
    }
  },
  {
    id: 2,
    title: "Product Feature Preferences",
    description: "Gathering feedback on proposed new features",
    status: "scheduled",
    participants: 0,
    targetParticipants: 12,
    duration: "60 minutes",
    createdAt: "2024-01-15",
    scheduledFor: "2024-01-18",
    moderator: "AI Moderator John",
    topics: ["Feature Priority", "Pricing", "Implementation"],
    sessions: 0,
    interactiveTools: {
      livePolling: true,
      whiteboard: false,
      reactions: true,
      screenShare: true,
      cardSorting: true,
      voting: true
    },
    aiModerator: {
      personality: "friendly",
      followUpDepth: 5,
      probingEnabled: true
    }
  },
  {
    id: 3,
    title: "Brand Perception Discussion",
    description: "Understanding how customers perceive our brand",
    status: "in-progress",
    participants: 6,
    targetParticipants: 10,
    duration: "75 minutes",
    createdAt: "2024-01-16",
    moderator: "AI Moderator Emma",
    topics: ["Brand Values", "Competitor Comparison", "Marketing Messages"],
    insights: {
      satisfaction: "N/A",
      keyFinding: "Session in progress",
      sentiment: {
        positive: 58,
        neutral: 30,
        negative: 12
      }
    },
    sessions: 1,
    interactiveTools: {
      livePolling: true,
      whiteboard: true,
      reactions: true,
      screenShare: false,
      cardSorting: false,
      voting: false
    },
    aiModerator: {
      personality: "empathetic",
      followUpDepth: 8,
      probingEnabled: true
    }
  }
];

export function FocusGroups({ onCreateFocusGroup, onSelectFocusGroup, showCreateDialog, onCreateDialogChange }: FocusGroupsProps) {
  const [focusGroups, setFocusGroups] = useState(mockFocusGroups);
  const [showInteractiveToolsDialog, setShowInteractiveToolsDialog] = useState(false);
  const [showAIModeratorDialog, setShowAIModeratorDialog] = useState(false);
  const [selectedGroupForConfig, setSelectedGroupForConfig] = useState<FocusGroup | null>(null);

  const handleDuplicateGroup = (group: FocusGroup) => {
    const duplicated: FocusGroup = {
      ...group,
      id: Math.max(...focusGroups.map(g => g.id)) + 1,
      title: `${group.title} (Copy)`,
      status: 'draft',
      participants: 0,
      sessions: 0,
      createdAt: new Date().toISOString().split('T')[0]
    };
    setFocusGroups([...focusGroups, duplicated]);
    toast.success(`Focus group duplicated: ${duplicated.title}`);
  };

  const handleDeleteGroup = (groupId: number) => {
    setFocusGroups(focusGroups.filter(g => g.id !== groupId));
    toast.success('Focus group deleted');
  };

  const handleStartSession = (group: FocusGroup) => {
    setFocusGroups(focusGroups.map(g => 
      g.id === group.id ? { ...g, status: 'in-progress' } : g
    ));
    toast.success(`Session started: ${group.title}`);
  };

  const totalParticipants = focusGroups.reduce((sum, g) => sum + g.participants, 0);
  const completedSessions = focusGroups.filter(g => g.status === 'completed').length;

  return (
    <div className="w-full max-w-[1920px] mx-auto space-y-6 px-2 sm:px-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground mb-2">Focus Groups</h1>
          <p className="text-muted-foreground">
            AI-moderated discussions with interactive tools and real-time analysis
          </p>
        </div>
        <Button 
          onClick={onCreateFocusGroup}
          className="bg-brand-orange hover:bg-brand-orange/90 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Focus Group
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Groups</p>
                <p className="text-2xl text-brand-orange">{focusGroups.length}</p>
              </div>
              <MessageSquare className="w-8 h-8 text-brand-orange" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Participants</p>
                <p className="text-2xl text-brand-orange">
                  {totalParticipants}
                </p>
              </div>
              <Users className="w-8 h-8 text-brand-orange" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed Sessions</p>
                <p className="text-2xl text-brand-orange">
                  {completedSessions}
                </p>
              </div>
              <BarChart2 className="w-8 h-8 text-brand-orange" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Focus Groups List */}
      <div className="space-y-4">
        <h2 className="text-foreground">Your Focus Groups</h2>
        
        <div className="grid grid-cols-1 gap-4">
          {focusGroups.map((group) => (
            <Card key={group.id} className="bg-card border border-border hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-3">
                          <h3 className="text-foreground">{group.title}</h3>
                          <Badge variant="outline" className={
                            group.status === 'completed' ? 'bg-green-500/10 text-green-600 border-green-500/30' :
                            group.status === 'in-progress' ? 'bg-brand-orange/10 text-brand-orange border-brand-orange/30' :
                            group.status === 'scheduled' ? 'bg-blue-500/10 text-blue-600 border-blue-500/30' :
                            'bg-muted text-muted-foreground border-border'
                          }>
                            {group.status === 'completed' ? 'Completed' :
                             group.status === 'in-progress' ? 'In Progress' :
                             group.status === 'scheduled' ? 'Scheduled' : 'Draft'}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {group.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {group.duration}
                          </span>
                          <span className="flex items-center gap-1">
                            <Brain className="w-3 h-3" />
                            {group.moderator}
                          </span>
                        </div>
                      </div>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onSelectFocusGroup(group)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => {
                            setSelectedGroupForConfig(group);
                            setShowInteractiveToolsDialog(true);
                          }}>
                            <Palette className="w-4 h-4 mr-2" />
                            Interactive Tools
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => {
                            setSelectedGroupForConfig(group);
                            setShowAIModeratorDialog(true);
                          }}>
                            <Brain className="w-4 h-4 mr-2" />
                            AI Moderator
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {group.status === 'scheduled' && (
                            <DropdownMenuItem onClick={() => handleStartSession(group)}>
                              <Play className="w-4 h-4 mr-2" />
                              Start Session
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => handleDuplicateGroup(group)}>
                            <Copy className="w-4 h-4 mr-2" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            className="text-destructive"
                            onClick={() => handleDeleteGroup(group.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Progress and Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Participants</span>
                          <span className="text-foreground">
                            {group.participants} / {group.targetParticipants}
                          </span>
                        </div>
                        <Progress value={(group.participants / group.targetParticipants) * 100} className="h-2" />
                        <p className="text-xs text-muted-foreground">
                          {Math.round((group.participants / group.targetParticipants) * 100)}% Full
                        </p>
                      </div>
                      
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Discussion Topics</p>
                        <div className="flex flex-wrap gap-1">
                          {group.topics.map((topic, i) => (
                            <Badge key={i} variant="outline" className="text-xs">{topic}</Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        {group.insights ? (
                          <>
                            <p className="text-sm text-muted-foreground">Key Insights</p>
                            <div className="space-y-1">
                              <p className="text-xs text-foreground">Satisfaction: {group.insights.satisfaction}</p>
                              <p className="text-xs text-foreground">{group.insights.keyFinding}</p>
                            </div>
                          </>
                        ) : (
                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">Status</p>
                            <p className="text-xs text-foreground">
                              {group.status === 'scheduled' && group.scheduledFor
                                ? `Scheduled for ${group.scheduledFor}`
                                : group.status === 'in-progress'
                                ? 'Session in progress'
                                : 'Ready to schedule'
                              }
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Sentiment & Tools */}
                    {group.insights?.sentiment && (
                      <div className="pt-2 border-t border-border">
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div>
                            <div className="flex items-center gap-2 justify-center mb-1">
                              <Smile className="w-4 h-4 text-green-600" />
                              <span className="text-xs text-muted-foreground">Positive</span>
                            </div>
                            <p className="text-sm text-foreground">{group.insights.sentiment.positive}%</p>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 justify-center mb-1">
                              <Meh className="w-4 h-4 text-yellow-600" />
                              <span className="text-xs text-muted-foreground">Neutral</span>
                            </div>
                            <p className="text-sm text-foreground">{group.insights.sentiment.neutral}%</p>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 justify-center mb-1">
                              <Frown className="w-4 h-4 text-red-600" />
                              <span className="text-xs text-muted-foreground">Negative</span>
                            </div>
                            <p className="text-sm text-foreground">{group.insights.sentiment.negative}%</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Interactive Tools Preview */}
                    {group.interactiveTools && (
                      <div className="pt-2 border-t border-border">
                        <p className="text-xs text-muted-foreground mb-2">Interactive Tools:</p>
                        <div className="flex flex-wrap gap-2">
                          {group.interactiveTools.livePolling && (
                            <Badge variant="outline" className="text-xs">
                              <BarChart2 className="w-3 h-3 mr-1" />
                              Live Polling
                            </Badge>
                          )}
                          {group.interactiveTools.whiteboard && (
                            <Badge variant="outline" className="text-xs">
                              <Palette className="w-3 h-3 mr-1" />
                              Whiteboard
                            </Badge>
                          )}
                          {group.interactiveTools.reactions && (
                            <Badge variant="outline" className="text-xs">
                              <ThumbsUp className="w-3 h-3 mr-1" />
                              Reactions
                            </Badge>
                          )}
                          {group.interactiveTools.voting && (
                            <Badge variant="outline" className="text-xs">
                              <Award className="w-3 h-3 mr-1" />
                              Voting
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {group.status === 'completed' && (
                        <Button 
                          size="sm" 
                          onClick={() => onSelectFocusGroup(group)}
                          className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View Results
                        </Button>
                      )}
                      {group.status === 'scheduled' && (
                        <Button 
                          size="sm"
                          onClick={() => handleStartSession(group)}
                          className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Start Session
                        </Button>
                      )}
                      {group.status === 'in-progress' && (
                        <Button 
                          size="sm"
                          variant="outline"
                          onClick={() => onSelectFocusGroup(group)}
                        >
                          <BarChart2 className="w-4 h-4 mr-2" />
                          Live Dashboard
                        </Button>
                      )}
                      <p className="text-xs text-muted-foreground ml-auto">
                        Created {new Date(group.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {focusGroups.length === 0 && (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-foreground mb-2">No focus groups yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first focus group to start gathering qualitative insights
              </p>
              <Button 
                onClick={onCreateFocusGroup}
                className="bg-brand-orange hover:bg-brand-orange/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Focus Group
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Interactive Tools Dialog */}
      <Dialog open={showInteractiveToolsDialog} onOpenChange={setShowInteractiveToolsDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Interactive Session Tools</DialogTitle>
            <DialogDescription>
              Enable tools for {selectedGroupForConfig?.title}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px]">
            <div className="grid grid-cols-2 gap-4 p-1">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2 text-base">
                    <BarChart2 className="w-5 h-5 text-brand-orange" />
                    Live Polling
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Real-time polls during discussion
                  </p>
                  <div className="p-3 border border-border rounded bg-muted/50">
                    <p className="text-xs text-foreground mb-2">Example poll:</p>
                    <p className="text-xs text-muted-foreground">"Which feature is most important?"</p>
                    <div className="mt-2 space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Feature A</span>
                        <span>45%</span>
                      </div>
                      <Progress value={45} className="h-1" />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="live-polling" defaultChecked={selectedGroupForConfig?.interactiveTools?.livePolling} />
                    <Label htmlFor="live-polling" className="cursor-pointer">Enable live polling</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2 text-base">
                    <Palette className="w-5 h-5 text-brand-gold" />
                    Collaboration Whiteboard
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Shared drawing and brainstorming canvas
                  </p>
                  <div className="aspect-video border border-border rounded bg-muted/50 flex items-center justify-center">
                    <Pencil className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="whiteboard" defaultChecked={selectedGroupForConfig?.interactiveTools?.whiteboard} />
                    <Label htmlFor="whiteboard" className="cursor-pointer">Enable whiteboard</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2 text-base">
                    <ThumbsUp className="w-5 h-5 text-chart-1" />
                    Reaction Tools
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Emoji reactions, raise hand, thumbs up/down
                  </p>
                  <div className="flex gap-2 text-2xl justify-center p-3 border border-border rounded bg-muted/50">
                    👍 👎 ❤️ 😊 ✋
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="reactions" defaultChecked={selectedGroupForConfig?.interactiveTools?.reactions} />
                    <Label htmlFor="reactions" className="cursor-pointer">Enable reactions</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2 text-base">
                    <Share2 className="w-5 h-5 text-chart-2" />
                    Screen Sharing
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Allow participants to share their screen
                  </p>
                  <div className="aspect-video border border-border rounded bg-muted/50 flex items-center justify-center">
                    <MessageSquare className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="screen-share" defaultChecked={selectedGroupForConfig?.interactiveTools?.screenShare} />
                    <Label htmlFor="screen-share" className="cursor-pointer">Enable screen sharing</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2 text-base">
                    <Target className="w-5 h-5 text-chart-3" />
                    Card Sorting
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Interactive card sorting exercises
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {['Card 1', 'Card 2', 'Card 3'].map((card, i) => (
                      <div key={i} className="p-2 border border-border rounded text-xs text-center bg-muted/50">
                        {card}
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="card-sorting" defaultChecked={selectedGroupForConfig?.interactiveTools?.cardSorting} />
                    <Label htmlFor="card-sorting" className="cursor-pointer">Enable card sorting</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2 text-base">
                    <Award className="w-5 h-5 text-chart-4" />
                    Priority Voting
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Vote and prioritize features or ideas
                  </p>
                  <div className="space-y-2">
                    {['Idea A', 'Idea B', 'Idea C'].map((idea, i) => (
                      <div key={i} className="flex items-center justify-between p-2 border border-border rounded">
                        <span className="text-xs">{idea}</span>
                        <Badge variant="outline">{3 - i} votes</Badge>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="voting" defaultChecked={selectedGroupForConfig?.interactiveTools?.voting} />
                    <Label htmlFor="voting" className="cursor-pointer">Enable priority voting</Label>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInteractiveToolsDialog(false)}>
              Cancel
            </Button>
            <Button 
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
              onClick={() => {
                toast.success('Interactive tools configured');
                setShowInteractiveToolsDialog(false);
              }}
            >
              Save Configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Moderator Dialog */}
      <Dialog open={showAIModeratorDialog} onOpenChange={setShowAIModeratorDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-brand-orange" />
              AI Moderator Settings
            </DialogTitle>
            <DialogDescription>
              Configure AI behavior for {selectedGroupForConfig?.title}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px]">
            <div className="space-y-6 p-1">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Moderator Personality</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Select defaultValue={selectedGroupForConfig?.aiModerator?.personality || "professional"}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="professional">Professional & Neutral</SelectItem>
                      <SelectItem value="friendly">Friendly & Conversational</SelectItem>
                      <SelectItem value="inquisitive">Inquisitive & Probing</SelectItem>
                      <SelectItem value="empathetic">Empathetic & Supportive</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Determines the tone and approach of the AI moderator
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Follow-up Depth</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Slider 
                      defaultValue={[selectedGroupForConfig?.aiModerator?.followUpDepth || 7]} 
                      max={10} 
                      step={1} 
                      className="mt-2" 
                    />
                    <div className="flex justify-between mt-2">
                      <span className="text-xs text-muted-foreground">Minimal (1)</span>
                      <span className="text-xs text-foreground">{selectedGroupForConfig?.aiModerator?.followUpDepth || 7}/10</span>
                      <span className="text-xs text-muted-foreground">Deep Dive (10)</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    How deeply the AI probes into responses
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Probing Techniques</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Ask "Why?"</p>
                      <p className="text-xs text-muted-foreground">Dig deeper into motivations</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Request Examples</p>
                      <p className="text-xs text-muted-foreground">Ask for specific instances</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Challenge Assumptions</p>
                      <p className="text-xs text-muted-foreground">Explore alternative viewpoints</p>
                    </div>
                    <Checkbox />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Seek Clarification</p>
                      <p className="text-xs text-muted-foreground">Ensure understanding</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Advanced Features</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Time Management</p>
                      <p className="text-xs text-muted-foreground">Keep discussion on schedule</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Bias Detection</p>
                      <p className="text-xs text-muted-foreground">Flag potential biases</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Sentiment Monitoring</p>
                      <p className="text-xs text-muted-foreground">Track emotional responses</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAIModeratorDialog(false)}>
              Cancel
            </Button>
            <Button 
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
              onClick={() => {
                toast.success('AI Moderator configured');
                setShowAIModeratorDialog(false);
              }}
            >
              Save Settings
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
