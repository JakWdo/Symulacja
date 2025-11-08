import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft } from 'lucide-react';
import { projectsApi } from '@/lib/api';
import type { Project } from '@/types';
import { Logo } from '@/components/ui/logo';

interface ProjectDetailProps {
  project: Project;
  onBack: () => void;
}

export function ProjectDetail({ project, onBack }: ProjectDetailProps) {
  const [formData, setFormData] = useState({
    name: project.name,
    description: project.description || '',
    target_sample_size: project.target_sample_size,
    target_audience: project.target_audience || '',
    research_objectives: project.research_objectives || '',
    additional_notes: project.additional_notes || ''
  });

  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: async () => {
      return projectsApi.update(project.id, {
        name: formData.name,
        description: formData.description,
        target_audience: formData.target_audience,
        research_objectives: formData.research_objectives,
        additional_notes: formData.additional_notes,
        target_sample_size: formData.target_sample_size,
        target_demographics: project.target_demographics
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['project', project.id] });
      onBack();
    },
    onError: (error) => {
      console.error('Failed to update project:', error);
      alert('Failed to save changes. Please try again.');
    }
  });

  const handleCancel = () => {
    onBack();
  };

  const handleSave = () => {
    updateMutation.mutate();
  };

  return (
      <div className="w-full h-full overflow-y-auto">
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

      {/* Setup Card */}
      <div className="space-y-6">
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
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-background border-border text-foreground"
                  />
                </div>
                <div>
                  <Label htmlFor="target-size">Target Sample Size</Label>
                  <Input
                    id="target-size"
                    type="number"
                    value={formData.target_sample_size}
                    onChange={(e) => setFormData({ ...formData, target_sample_size: parseInt(e.target.value) || 0 })}
                    className="bg-background border-border text-foreground"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="project-description">Description</Label>
                <Textarea
                  id="project-description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="bg-background border-border text-foreground"
                  rows={3}
                />
              </div>

              {/* Target Audience */}
              <div>
                <Label htmlFor="target-audience">Target Audience</Label>
                <Textarea
                  id="target-audience"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  placeholder="Describe your target audience demographics..."
                  className="bg-background border-border text-foreground"
                  rows={6}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="research-objectives">Research Objectives</Label>
                  <Textarea
                    id="research-objectives"
                    value={formData.research_objectives}
                    onChange={(e) => setFormData({ ...formData, research_objectives: e.target.value })}
                    placeholder="Define what you want to learn from this research project..."
                    className="bg-background border-border text-foreground"
                    rows={4}
                  />
                </div>
                <div>
                  <Label htmlFor="additional-notes">Additional Notes</Label>
                  <Textarea
                    id="additional-notes"
                    value={formData.additional_notes}
                    onChange={(e) => setFormData({ ...formData, additional_notes: e.target.value })}
                    placeholder="Any additional information about the project..."
                    className="bg-background border-border text-foreground"
                    rows={4}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="outline"
                  className="border-border text-muted-foreground hover:text-foreground"
                  onClick={handleCancel}
                  disabled={updateMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  className="bg-brand hover:bg-brand/90 text-brand-foreground"
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                >
                  {updateMutation.isPending ? (
                    <>
                      <Logo className="w-4 h-4 mr-2" spinning />
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
