import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { ArrowLeft, Settings as SettingsIcon, Users, MessageSquare, BarChart3 } from 'lucide-react';

interface ProjectDetailProps {
  project: any;
  onBack: () => void;
  onNavigate?: (view: string) => void;
}

export function ProjectDetail({ project, onBack, onNavigate }: ProjectDetailProps) {
  // Project setup state can be added here if needed

  // Project-specific functionality can be added here

  return (
    <div className="max-w-7xl mx-auto space-y-6">
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
        </TabsList>

        {/* Setup Tab */}
        <TabsContent value="setup" className="space-y-6">
          <Card className="bg-card border border-border shadow-elevated">
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
                  <Label htmlFor="project-status">Status</Label>
                  <Input
                    id="project-status"
                    defaultValue={project.status}
                    className="bg-input-background border-border text-foreground"
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="project-description">Description</Label>
                <Textarea
                  id="project-description"
                  defaultValue={project.description}
                  className="bg-input-background border-border text-foreground"
                  rows={3}
                />
              </div>

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
                  <Label htmlFor="target-audience">Target Audience</Label>
                  <Textarea
                    id="target-audience"
                    placeholder="Describe your target demographic and user base..."
                    className="bg-input-background border-border text-foreground"
                    rows={4}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <Label htmlFor="research-timeline">Timeline</Label>
                  <Input
                    id="research-timeline"
                    placeholder="e.g., 4-6 weeks"
                    className="bg-input-background border-border text-foreground"
                  />
                </div>
                <div>
                  <Label htmlFor="project-budget">Budget</Label>
                  <Input
                    id="project-budget"
                    placeholder="e.g., $5,000"
                    className="bg-input-background border-border text-foreground"
                  />
                </div>
                <div>
                  <Label htmlFor="project-team">Team Size</Label>
                  <Input
                    id="project-team"
                    placeholder="e.g., 3-5 researchers"
                    className="bg-input-background border-border text-foreground"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" className="border-border text-muted-foreground hover:text-foreground">
                  Cancel
                </Button>
                <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-card border border-border shadow-elevated hover:shadow-floating transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-brand-orange/10 rounded-lg flex items-center justify-center">
                    <Users className="w-6 h-6 text-brand-orange" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg text-card-foreground">
                      Create Personas
                    </h3>
                    <p className="text-sm text-muted-foreground">Generate AI personas for this project</p>
                  </div>
                  <Button 
                    onClick={() => onNavigate?.('personas')}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  >
                    Go to Personas
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border border-border shadow-elevated hover:shadow-floating transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-brand-orange/10 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-brand-orange" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg text-card-foreground">
                      Run Focus Groups
                    </h3>
                    <p className="text-sm text-muted-foreground">Conduct qualitative research sessions</p>
                  </div>
                  <Button 
                    onClick={() => onNavigate?.('focus-groups')}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  >
                    Go to Focus Groups
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Surveys Panel */}
          <Card className="bg-card border border-border shadow-elevated hover:shadow-floating transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-brand-orange/10 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-brand-orange" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg text-card-foreground">
                    Create Surveys
                  </h3>
                  <p className="text-sm text-muted-foreground">Build quantitative research surveys for data collection</p>
                </div>
                <Button 
                  onClick={() => onNavigate?.('surveys')}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground"
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