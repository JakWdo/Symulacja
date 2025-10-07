import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { MoreVertical, Plus, Users, Eye, BarChart3, Play } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';

interface SurveysProps {
  onCreateSurvey: () => void;
  onSelectSurvey: (survey: any) => void;
  showCreateDialog: boolean;
  onCreateDialogChange: (show: boolean) => void;
}

const mockSurveys = [
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
      sentiment: "73% Positive"
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
    }
  }
];



export function Surveys({ onCreateSurvey, onSelectSurvey, showCreateDialog, onCreateDialogChange }: SurveysProps) {
  const [surveys] = useState(mockSurveys);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Synthetic Surveys</h1>
          <p className="text-muted-foreground">
            Generate quantitative insights from virtual respondents perfectly matched to your target audience
          </p>
        </div>
        <Button 
          onClick={onCreateSurvey}
          className="bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create New Survey
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Surveys</p>
                <p className="text-2xl brand-orange">{surveys.length}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Responses</p>
                <p className="text-2xl brand-orange">
                  {surveys.reduce((sum, survey) => sum + survey.responses, 0).toLocaleString()}
                </p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Surveys List */}
      <div className="space-y-4">
        <h2 className="text-xl text-foreground">Your Surveys</h2>
        
        <div className="grid grid-cols-1 gap-4">
          {surveys.map((survey) => (
            <Card key={survey.id} className="bg-card border border-border hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2">
                          <h3 className="text-lg text-card-foreground">{survey.title}</h3>
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
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={() => onSelectSurvey(survey)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Results
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <BarChart3 className="w-4 h-4 mr-2" />
                            Duplicate Survey
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Progress and Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Progress</span>
                          <span className="text-card-foreground">
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
                          <p className="text-xs text-card-foreground">Age: {survey.demographics.age}</p>
                          <p className="text-xs text-card-foreground">Gender: {survey.demographics.gender}</p>
                          <p className="text-xs text-card-foreground">Income: {survey.demographics.income}</p>
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        {survey.insights ? (
                          <>
                            <p className="text-sm text-muted-foreground">Key Insights</p>
                            <div className="space-y-1">
                              <p className="text-xs text-card-foreground">{survey.insights.topChoice}</p>
                              <p className="text-xs text-card-foreground">{survey.insights.sentiment}</p>
                            </div>
                          </>
                        ) : (
                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">Status</p>
                            <p className="text-xs text-card-foreground">
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

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-2">
                      {survey.status === 'completed' && (
                        <Button 
                          size="sm" 
                          onClick={() => onSelectSurvey(survey)}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View Results
                        </Button>
                      )}
                      {survey.status === 'draft' && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="border-border text-muted-foreground hover:text-foreground"
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Launch
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
              <h3 className="text-lg text-card-foreground mb-2">No surveys yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first synthetic survey to start collecting quantitative data
              </p>
              <Button 
                onClick={onCreateSurvey}
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create First Survey
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}