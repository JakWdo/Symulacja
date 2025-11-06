import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Slider } from './ui/slider';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { MoreVertical, Plus, Users, Eye, BarChart3, Play, Copy, Trash2, TrendingUp, Grid3x3, ArrowUpDown, Image, Sliders, CheckCircle2, Zap, Bot, Clock, AlertCircle, Settings } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { toast } from 'sonner@2.0.3';

interface SurveysProps {
  onCreateSurvey: () => void;
  onSelectSurvey: (survey: any) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

interface Survey {
  id: number;
  title: string;
  project: string;
  status: string;
  responses: number;
  targetResponses: number;
  progress: number;
  createdAt: string;
  completedAt?: string;
  demographics: {
    age: string;
    gender: string;
    income: string;
  };
  insights?: {
    topChoice: string;
    sentiment: string;
    nps?: number;
  };
  questionTypes?: {
    nps: number;
    matrix: number;
    ranking: number;
    imageChoice: number;
    slider: number;
    multipleChoice: number;
  };
  logic?: {
    skipLogic: boolean;
    displayLogic: boolean;
    piping: boolean;
  };
  qualityControl?: {
    attentionChecks: number;
    botDetection: boolean;
    minResponseTime: number;
    qualityScore: number;
  };
}

const mockSurveys: Survey[] = [
  {
    id: 1,
    title: "E-commerce Platform Preferences",
    project: "Mobile App Launch Research",
    status: "completed",
    responses: 1000,
    targetResponses: 1000,
    progress: 100,
    createdAt: "2024-01-15",
    completedAt: "2024-01-15",
    demographics: {
      age: "18-65",
      gender: "All",
      income: "$30k+"
    },
    insights: {
      topChoice: "Ease of use (45%)",
      sentiment: "73% Positive",
      nps: 42
    },
    questionTypes: {
      nps: 1,
      matrix: 2,
      ranking: 1,
      imageChoice: 0,
      slider: 3,
      multipleChoice: 8
    },
    logic: {
      skipLogic: true,
      displayLogic: true,
      piping: false
    },
    qualityControl: {
      attentionChecks: 2,
      botDetection: true,
      minResponseTime: 60,
      qualityScore: 94
    }
  },
  {
    id: 2,
    title: "Feature Priority Survey",
    project: "Product Development Study", 
    status: "running",
    responses: 742,
    targetResponses: 1500,
    progress: 49,
    createdAt: "2024-01-16",
    demographics: {
      age: "25-45",
      gender: "All",
      income: "$50k+"
    },
    questionTypes: {
      nps: 2,
      matrix: 3,
      ranking: 2,
      imageChoice: 1,
      slider: 4,
      multipleChoice: 12
    },
    logic: {
      skipLogic: true,
      displayLogic: false,
      piping: true
    },
    qualityControl: {
      attentionChecks: 3,
      botDetection: true,
      minResponseTime: 90,
      qualityScore: 91
    }
  },
  {
    id: 3,
    title: "Brand Perception Study",
    project: "Marketing Research",
    status: "draft", 
    responses: 0,
    targetResponses: 800,
    progress: 0,
    createdAt: "2024-01-17",
    demographics: {
      age: "18-34",
      gender: "Female",
      income: "$40k+"
    },
    questionTypes: {
      nps: 1,
      matrix: 4,
      ranking: 3,
      imageChoice: 2,
      slider: 2,
      multipleChoice: 15
    },
    logic: {
      skipLogic: true,
      displayLogic: true,
      piping: true
    }
  }
];

export function Surveys({ onCreateSurvey, onSelectSurvey, showCreateDialog, onCreateDialogChange }: SurveysProps) {
  const [surveys, setSurveys] = useState(mockSurveys);
  const [showQuestionTypesDialog, setShowQuestionTypesDialog] = useState(false);
  const [showLogicDialog, setShowLogicDialog] = useState(false);
  const [showQualityDialog, setShowQualityDialog] = useState(false);
  const [selectedSurveyForConfig, setSelectedSurveyForConfig] = useState<Survey | null>(null);

  const handleDuplicateSurvey = (survey: Survey) => {
    const duplicated: Survey = {
      ...survey,
      id: Math.max(...surveys.map(s => s.id)) + 1,
      title: `${survey.title} (Copy)`,
      status: 'draft',
      responses: 0,
      progress: 0,
      createdAt: new Date().toISOString().split('T')[0]
    };
    setSurveys([...surveys, duplicated]);
    toast.success(`Survey duplicated: ${duplicated.title}`);
  };

  const handleDeleteSurvey = (surveyId: number) => {
    setSurveys(surveys.filter(s => s.id !== surveyId));
    toast.success('Survey deleted');
  };

  const handleLaunchSurvey = (survey: Survey) => {
    const updatedSurveys = surveys.map(s => 
      s.id === survey.id ? { ...s, status: 'running' } : s
    );
    setSurveys(updatedSurveys);
    toast.success(`Survey launched: ${survey.title}`);
  };

  const totalResponses = surveys.reduce((sum, s) => sum + s.responses, 0);
  const avgQualityScore = surveys
    .filter(s => s.qualityControl)
    .reduce((sum, s) => sum + (s.qualityControl?.qualityScore || 0), 0) / 
    surveys.filter(s => s.qualityControl).length;

  return (
    <div className="w-full max-w-[1920px] mx-auto space-y-6 px-2 sm:px-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground mb-2">Surveys</h1>
          <p className="text-muted-foreground">
            Generate quantitative insights with advanced question types and logic
          </p>
        </div>
        <Button 
          onClick={onCreateSurvey}
          className="bg-brand-orange hover:bg-brand-orange/90 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Survey
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Surveys</p>
                <p className="text-2xl text-brand-orange">{surveys.length}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-brand-orange" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Responses</p>
                <p className="text-2xl text-brand-orange">
                  {totalResponses.toLocaleString()}
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
                <p className="text-sm text-muted-foreground">Avg Quality Score</p>
                <p className="text-2xl text-brand-orange">
                  {avgQualityScore ? avgQualityScore.toFixed(0) : '—'}%
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-brand-orange" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Surveys List */}
      <div className="space-y-4">
        <h2 className="text-foreground">Your Surveys</h2>
        
        <div className="grid grid-cols-1 gap-4">
          {surveys.map((survey) => (
            <Card key={survey.id} className="bg-card border border-border hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-3">
                          <h3 className="text-foreground">{survey.title}</h3>
                          <Badge variant="outline" className={
                            survey.status === 'completed' ? 'bg-green-500/10 text-green-600 border-green-500/30' :
                            survey.status === 'running' ? 'bg-brand-orange/10 text-brand-orange border-brand-orange/30' :
                            'bg-muted text-muted-foreground border-border'
                          }>
                            {survey.status === 'completed' ? 'Completed' :
                             survey.status === 'running' ? 'Running' : 'Draft'}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Project: {survey.project}
                        </p>
                      </div>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onSelectSurvey(survey)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Results
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => {
                            setSelectedSurveyForConfig(survey);
                            setShowQuestionTypesDialog(true);
                          }}>
                            <Grid3x3 className="w-4 h-4 mr-2" />
                            Question Types
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => {
                            setSelectedSurveyForConfig(survey);
                            setShowLogicDialog(true);
                          }}>
                            <Zap className="w-4 h-4 mr-2" />
                            Survey Logic
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => {
                            setSelectedSurveyForConfig(survey);
                            setShowQualityDialog(true);
                          }}>
                            <CheckCircle2 className="w-4 h-4 mr-2" />
                            Quality Control
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => handleDuplicateSurvey(survey)}>
                            <Copy className="w-4 h-4 mr-2" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => handleDeleteSurvey(survey.id)}
                            className="text-destructive"
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
                          <span className="text-muted-foreground">Progress</span>
                          <span className="text-foreground">
                            {survey.responses.toLocaleString()} / {survey.targetResponses.toLocaleString()}
                          </span>
                        </div>
                        <Progress value={survey.progress} className="h-2" />
                        <p className="text-xs text-muted-foreground">
                          {survey.progress}% Complete
                        </p>
                      </div>
                      
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Demographics</p>
                        <div className="space-y-1">
                          <p className="text-xs text-foreground">Age: {survey.demographics.age}</p>
                          <p className="text-xs text-foreground">Gender: {survey.demographics.gender}</p>
                          <p className="text-xs text-foreground">Income: {survey.demographics.income}</p>
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        {survey.insights ? (
                          <>
                            <p className="text-sm text-muted-foreground">Key Insights</p>
                            <div className="space-y-1">
                              <p className="text-xs text-foreground">{survey.insights.topChoice}</p>
                              <p className="text-xs text-foreground">{survey.insights.sentiment}</p>
                              {survey.insights.nps && (
                                <p className="text-xs text-foreground">NPS: {survey.insights.nps}</p>
                              )}
                            </div>
                          </>
                        ) : (
                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">Status</p>
                            <p className="text-xs text-foreground">
                              {survey.status === 'running' 
                                ? `Processing respondent ${survey.responses}...`
                                : survey.status === 'draft'
                                ? 'Ready to launch'
                                : 'Completed'
                              }
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Question Types Overview */}
                    {survey.questionTypes && (
                      <div className="pt-2 border-t border-border">
                        <p className="text-xs text-muted-foreground mb-2">Question Types:</p>
                        <div className="flex flex-wrap gap-2">
                          {survey.questionTypes.nps > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              NPS ({survey.questionTypes.nps})
                            </Badge>
                          )}
                          {survey.questionTypes.matrix > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <Grid3x3 className="w-3 h-3 mr-1" />
                              Matrix ({survey.questionTypes.matrix})
                            </Badge>
                          )}
                          {survey.questionTypes.ranking > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <ArrowUpDown className="w-3 h-3 mr-1" />
                              Ranking ({survey.questionTypes.ranking})
                            </Badge>
                          )}
                          {survey.questionTypes.slider > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <Sliders className="w-3 h-3 mr-1" />
                              Slider ({survey.questionTypes.slider})
                            </Badge>
                          )}
                          {survey.questionTypes.multipleChoice > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              Multiple Choice ({survey.questionTypes.multipleChoice})
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Quality Score */}
                    {survey.qualityControl && (
                      <div className="pt-2 border-t border-border">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground">Quality Score:</span>
                          <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/30">
                            {survey.qualityControl.qualityScore}%
                          </Badge>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {survey.status === 'completed' && (
                        <Button 
                          size="sm" 
                          onClick={() => onSelectSurvey(survey)}
                          className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View Results
                        </Button>
                      )}
                      {survey.status === 'draft' && (
                        <Button 
                          size="sm" 
                          className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                          onClick={() => handleLaunchSurvey(survey)}
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Launch Survey
                        </Button>
                      )}
                      {survey.status === 'running' && (
                        <Button 
                          size="sm" 
                          onClick={() => onSelectSurvey(survey)}
                          variant="outline"
                        >
                          <BarChart3 className="w-4 h-4 mr-2" />
                          View Progress
                        </Button>
                      )}
                      <p className="text-xs text-muted-foreground ml-auto">
                        Created {new Date(survey.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {surveys.length === 0 && (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-foreground mb-2">No surveys yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first survey to start collecting quantitative data
              </p>
              <Button 
                onClick={onCreateSurvey}
                className="bg-brand-orange hover:bg-brand-orange/90 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Survey
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Question Types Dialog */}
      <Dialog open={showQuestionTypesDialog} onOpenChange={setShowQuestionTypesDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Advanced Question Types</DialogTitle>
            <DialogDescription>
              Configure question types for {selectedSurveyForConfig?.title}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px]">
            <div className="grid grid-cols-2 gap-4 p-1">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-brand-orange" />
                    NPS Question
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Net Promoter Score with auto-categorization (Promoters, Passives, Detractors)
                  </p>
                  <div className="flex gap-1">
                    {[0,1,2,3,4,5,6,7,8,9,10].map(n => (
                      <div key={n} className="flex-1 h-8 border border-border rounded flex items-center justify-center text-xs">
                        {n}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    0-6: Detractors | 7-8: Passives | 9-10: Promoters
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <Grid3x3 className="w-5 h-5 text-brand-gold" />
                    Matrix/Grid
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Multiple items rated on same scale
                  </p>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <div className="flex justify-between">
                      <span>Feature A</span>
                      <span>○ ○ ○ ○ ○</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Feature B</span>
                      <span>○ ○ ○ ○ ○</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Feature C</span>
                      <span>○ ○ ○ ○ ○</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <ArrowUpDown className="w-5 h-5 text-chart-1" />
                    Ranking
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Drag to rank items in order of preference
                  </p>
                  <div className="space-y-2">
                    {['Option 1', 'Option 2', 'Option 3'].map((opt, i) => (
                      <div key={i} className="p-2 border border-border rounded text-xs flex items-center gap-2">
                        <ArrowUpDown className="w-3 h-3" />
                        {opt}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <Image className="w-5 h-5 text-chart-2" />
                    Image Choice
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Visual selection with images
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {[1,2,3,4].map(n => (
                      <div key={n} className="aspect-square border border-border rounded bg-muted" />
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <Sliders className="w-5 h-5 text-chart-3" />
                    Slider/Scale
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Continuous numeric scale with labels
                  </p>
                  <div className="space-y-4">
                    <Slider defaultValue={[50]} max={100} step={1} />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Not at all</span>
                      <span>Extremely</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-chart-4" />
                    Multiple Choice
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Standard single or multiple selection
                  </p>
                  <div className="space-y-2">
                    {['Option A', 'Option B', 'Option C'].map((opt, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <Checkbox />
                        <span className="text-sm">{opt}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowQuestionTypesDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Survey Logic Dialog */}
      <Dialog open={showLogicDialog} onOpenChange={setShowLogicDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Survey Logic Configuration</DialogTitle>
            <DialogDescription>
              Set up advanced logic for {selectedSurveyForConfig?.title}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px]">
            <div className="space-y-6 p-1">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Skip Logic</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Skip questions based on previous answers
                  </p>
                  <div className="space-y-3 p-3 border border-border rounded bg-muted/50">
                    <div className="text-sm">
                      <p className="text-foreground mb-2">Example:</p>
                      <p className="text-muted-foreground">
                        IF "Do you use our product?" = "No"<br/>
                        THEN skip to "Why not?" question
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="skip-logic" defaultChecked={selectedSurveyForConfig?.logic?.skipLogic} />
                    <Label htmlFor="skip-logic">Enable skip logic</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Display Logic</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Show/hide questions based on conditions
                  </p>
                  <div className="space-y-3 p-3 border border-border rounded bg-muted/50">
                    <div className="text-sm">
                      <p className="text-foreground mb-2">Example:</p>
                      <p className="text-muted-foreground">
                        SHOW "Premium features rating"<br/>
                        ONLY IF "Plan type" = "Premium"
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="display-logic" defaultChecked={selectedSurveyForConfig?.logic?.displayLogic} />
                    <Label htmlFor="display-logic">Enable display logic</Label>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Piping</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Insert previous answers into questions
                  </p>
                  <div className="space-y-3 p-3 border border-border rounded bg-muted/50">
                    <div className="text-sm">
                      <p className="text-foreground mb-2">Example:</p>
                      <p className="text-muted-foreground">
                        Q1: "What feature do you use most?" → Answer: "Analytics"<br/>
                        Q2: "How satisfied are you with [Analytics]?"
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox id="piping" defaultChecked={selectedSurveyForConfig?.logic?.piping} />
                    <Label htmlFor="piping">Enable piping</Label>
                  </div>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLogicDialog(false)}>
              Cancel
            </Button>
            <Button 
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
              onClick={() => {
                toast.success('Logic rules saved');
                setShowLogicDialog(false);
              }}
            >
              Save Logic
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Quality Control Dialog */}
      <Dialog open={showQualityDialog} onOpenChange={setShowQualityDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Quality Control Settings</DialogTitle>
            <DialogDescription>
              Ensure high-quality responses for {selectedSurveyForConfig?.title}
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="h-[500px]">
            <div className="space-y-6 p-1">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-brand-orange" />
                    Attention Checks
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Insert questions to verify respondent attention
                  </p>
                  <div>
                    <Label>Number of attention checks</Label>
                    <Slider 
                      defaultValue={[selectedSurveyForConfig?.qualityControl?.attentionChecks || 2]} 
                      max={5} 
                      step={1} 
                      className="mt-2" 
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      {selectedSurveyForConfig?.qualityControl?.attentionChecks || 2} checks recommended
                    </p>
                  </div>
                  <div className="p-3 border border-border rounded bg-muted/50">
                    <p className="text-sm text-foreground mb-2">Example attention check:</p>
                    <p className="text-xs text-muted-foreground italic">
                      "To ensure quality, please select 'Strongly Agree' for this question."
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <Clock className="w-5 h-5 text-brand-gold" />
                    Response Time Monitoring
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Minimum response time (seconds)</Label>
                    <Slider 
                      defaultValue={[selectedSurveyForConfig?.qualityControl?.minResponseTime || 60]} 
                      max={300} 
                      step={10} 
                      className="mt-2" 
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      {selectedSurveyForConfig?.qualityControl?.minResponseTime || 60} seconds
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Flag responses completed too quickly
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground flex items-center gap-2">
                    <Bot className="w-5 h-5 text-chart-1" />
                    Bot Detection
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Enable bot detection</p>
                      <p className="text-xs text-muted-foreground">Using behavioral analysis</p>
                    </div>
                    <Checkbox defaultChecked={selectedSurveyForConfig?.qualityControl?.botDetection} />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">CAPTCHA verification</p>
                      <p className="text-xs text-muted-foreground">For suspicious activity</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground">Duplicate prevention</p>
                      <p className="text-xs text-muted-foreground">Block repeat submissions</p>
                    </div>
                    <Checkbox defaultChecked />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-foreground">Quality Score Threshold</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Minimum quality score to include</Label>
                    <Slider defaultValue={[70]} max={100} step={5} className="mt-2" />
                    <div className="flex justify-between mt-1">
                      <span className="text-xs text-muted-foreground">Low (60%)</span>
                      <span className="text-xs text-muted-foreground">High (90%)</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Responses below this threshold will be flagged for review
                  </p>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowQualityDialog(false)}>
              Cancel
            </Button>
            <Button 
              className="bg-brand-orange hover:bg-brand-orange/90 text-white"
              onClick={() => {
                toast.success('Quality control settings saved');
                setShowQualityDialog(false);
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
