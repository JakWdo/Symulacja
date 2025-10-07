import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Users, MessageSquare, Settings as SettingsIcon, BarChart3 } from 'lucide-react';
import type { Project } from '@/types';

interface ProjectDetailProps {
  project: Project;
  onBack: () => void;
  onNavigate?: (view: string) => void;
}

export function ProjectDetail({ project, onBack, onNavigate }: ProjectDetailProps) {
  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div>
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Projects
        </Button>
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">{project.name}</h1>
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
        </TabsList>

        {/* Setup Tab */}
        <TabsContent value="setup" className="space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-foreground">Project Configuration</CardTitle>
              <p className="text-muted-foreground">Configure your project settings and research objectives</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="project-name">Project Name</Label>
                  <Input
                    id="project-name"
                    defaultValue={project.name}
                    className="bg-input-background border-border text-foreground"
                  />
                </div>
                <div>
                  <Label htmlFor="target-size">Target Sample Size</Label>
                  <Input
                    id="target-size"
                    defaultValue={project.target_sample_size}
                    className="bg-input-background border-border text-foreground"
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
                />
              </div>

              {/* Target Demographics */}
              {project.target_demographics && (
                <div>
                  <Label>Target Audience</Label>
                  <div className="mt-2 p-4 bg-muted rounded-lg border border-border">
                    <div className="space-y-2">
                      {project.target_demographics.age_group && (
                        <div>
                          <p className="text-xs text-muted-foreground">Age Groups:</p>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {Object.entries(project.target_demographics.age_group).map(([group, value]) => (
                              <Badge key={group} variant="secondary" className="bg-muted text-muted-foreground">
                                {group}: {Math.round((value as number) * 100)}%
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {project.target_demographics.gender && (
                        <div>
                          <p className="text-xs text-muted-foreground">Gender Distribution:</p>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {Object.entries(project.target_demographics.gender).map(([gender, value]) => (
                              <Badge key={gender} variant="secondary" className="bg-muted text-muted-foreground">
                                {gender}: {Math.round((value as number) * 100)}%
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="research-objectives">Research Objectives</Label>
                  <Textarea
                    id="research-objectives"
                    placeholder="Define what you want to learn from this research project..."
                    className="bg-input-background border-border text-foreground"
                    rows={4}
                  />
                </div>
                <div>
                  <Label htmlFor="target-audience">Additional Notes</Label>
                  <Textarea
                    id="target-audience"
                    placeholder="Any additional information about the project..."
                    className="bg-input-background border-border text-foreground"
                    rows={4}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" className="border-border text-muted-foreground hover:text-foreground">
                  Cancel
                </Button>
                <Button className="bg-[#F27405] hover:bg-[#F27405]/90 text-white">
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions - Navigation Panels */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-card border border-border shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-[#F27405]/10 rounded-lg flex items-center justify-center">
                    <Users className="w-6 h-6 text-[#F27405]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg text-card-foreground">
                      Create Personas
                    </h3>
                    <p className="text-sm text-muted-foreground">Generate AI personas for this project</p>
                  </div>
                  <Button
                    onClick={() => onNavigate?.('personas')}
                    className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                  >
                    Go to Personas
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border border-border shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-[#F27405]/10 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-[#F27405]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg text-card-foreground">
                      Run Focus Groups
                    </h3>
                    <p className="text-sm text-muted-foreground">Conduct qualitative research sessions</p>
                  </div>
                  <Button
                    onClick={() => onNavigate?.('focus-groups')}
                    className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                  >
                    Go to Focus Groups
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Surveys Panel */}
          <Card className="bg-card border border-border shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#F27405]/10 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-[#F27405]" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg text-card-foreground">
                    Create Surveys
                  </h3>
                  <p className="text-sm text-muted-foreground">Build quantitative research surveys for data collection</p>
                </div>
                <Button
                  onClick={() => onNavigate?.('surveys')}
                  className="bg-[#F27405] hover:bg-[#F27405]/90 text-white"
                >
                  Go to Surveys
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
