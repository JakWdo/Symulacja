import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { MoreVertical, Plus, Users, MessageSquare, Eye, Settings } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';

interface FocusGroupsProps {
  onCreateFocusGroup: () => void;
  onSelectFocusGroup: (focusGroup: any) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

const mockFocusGroups = [
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
      keyFinding: "Navigation needs simplification"
    },
    sessions: 1
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
    sessions: 0
  },
  {
    id: 3,
    title: "Brand Perception Study",
    description: "Understanding how customers perceive our brand",
    status: "running",
    participants: 6,
    targetParticipants: 10,
    duration: "45 minutes",
    createdAt: "2024-01-16",
    moderator: "AI Moderator Emma",
    topics: ["Brand Values", "Competition", "Trust"],
    sessions: 1
  },
  {
    id: 4,
    title: "E-commerce Checkout Flow",  
    description: "Testing the new checkout process with users",
    status: "draft",
    participants: 0,
    targetParticipants: 6,
    duration: "75 minutes",
    createdAt: "2024-01-17",
    moderator: "AI Moderator Alex",
    topics: ["Usability", "Trust Signals", "Payment Options"],
    sessions: 0
  }
];



export function FocusGroups({ onCreateFocusGroup, onSelectFocusGroup, showCreateDialog, onCreateDialogChange }: FocusGroupsProps) {
  const [focusGroups] = useState(mockFocusGroups);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
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
          className="bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Focus Group
        </Button>
      </div>

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
                  {focusGroups.reduce((sum, fg) => sum + fg.participants, 0)}
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
            <Card key={focusGroup.id} className="bg-card border border-border hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2">
                          <h3 className="text-lg text-card-foreground">{focusGroup.title}</h3>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {focusGroup.description}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Moderator: {focusGroup.moderator} • Duration: {focusGroup.duration}
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
                          <DropdownMenuItem>
                            <MessageSquare className="w-4 h-4 mr-2" />
                            Duplicate Group
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
                            {focusGroup.participants} / {focusGroup.targetParticipants}
                          </span>
                        </div>
                        <Progress 
                          value={(focusGroup.participants / focusGroup.targetParticipants) * 100} 
                          className="h-2" 
                        />
                        <p className="text-xs text-muted-foreground">
                          {Math.round((focusGroup.participants / focusGroup.targetParticipants) * 100)}% Full
                        </p>
                      </div>
                      
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Discussion Topics</p>
                        <div className="flex flex-wrap gap-1">
                          {focusGroup.topics.slice(0, 3).map((topic, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        {focusGroup.insights ? (
                          <>
                            <p className="text-sm text-muted-foreground">Key Results</p>
                            <div className="space-y-1">
                              <p className="text-xs text-card-foreground">Satisfaction: {focusGroup.insights.satisfaction}</p>
                              <p className="text-xs text-card-foreground">{focusGroup.insights.keyFinding}</p>
                            </div>
                          </>
                        ) : (
                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">Status</p>
                            <p className="text-xs text-card-foreground">
                              {focusGroup.status === 'running' 
                                ? `In progress (${focusGroup.participants} participants)`
                                : focusGroup.status === 'scheduled'
                                ? `Scheduled for ${new Date(focusGroup.scheduledFor).toLocaleDateString()}`
                                : focusGroup.status === 'draft'
                                ? 'Ready to schedule'
                                : 'Completed'
                              }
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {focusGroup.status === 'completed' && (
                        <Button 
                          size="sm" 
                          onClick={() => onSelectFocusGroup(focusGroup)}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View Focus Group
                        </Button>
                      )}
                      {(focusGroup.status === 'draft' || focusGroup.status === 'scheduled') && (
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
                          className="bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View Focus Group
                        </Button>
                      )}
                      <p className="text-xs text-muted-foreground ml-auto">
                        Created {new Date(focusGroup.createdAt).toLocaleDateString()}
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
              <h3 className="text-lg text-card-foreground mb-2">No focus groups yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first focus group to start conducting qualitative research
              </p>
              <Button 
                onClick={onCreateFocusGroup}
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Focus Group
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}