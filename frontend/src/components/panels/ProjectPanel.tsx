import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { projectsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { Plus, FolderOpen, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/Button'; // Import Button
import type { Project } from '@/types';

// Komponent formularza do tworzenia projektu
function CreateProjectForm({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const queryClient = useQueryClient();

  const createProjectMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      onClose(); // Zamknij formularz po sukcesie
    },
    onError: (error) => {
      alert(`Error creating project: ${error.message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Project name is required.');
      return;
    }
    // Domyślna demografia - możesz to rozbudować
    const defaultDemographics = {
        age: { "18-24": 0.2, "25-34": 0.3, "35-55": 0.5 },
        gender: { "male": 0.5, "female": 0.5 },
    };

    createProjectMutation.mutate({
      name,
      description,
      target_demographics: defaultDemographics,
      target_sample_size: 100,
    });
  };

  return (
    <div className="p-4 border-t border-slate-200/50">
      <h4 className="font-semibold text-slate-800 mb-3">Create a New Project</h4>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Project Name"
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Project Description (optional)"
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          rows={3}
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm" isLoading={createProjectMutation.isPending}>
            Create
          </Button>
        </div>
      </form>
    </div>
  );
}


export function ProjectPanel() {
  const { activePanel, setActivePanel, setSelectedProject } = useAppStore();
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await projectsApi.getAll();
      return response.data;
    },
  });

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    setActivePanel(null);
  };

  return (
    <FloatingPanel
      isOpen={activePanel === 'projects'}
      onClose={() => setActivePanel(null)}
      title="Projects"
      position="left"
      size="lg"
    >
      <div className="p-4 space-y-4">
        {/* Create Button */}
        {!showCreateForm && (
            <button
            onClick={() => setShowCreateForm(true)}
            className="w-full floating-button flex items-center justify-center gap-2 py-3"
            >
            <Plus className="w-5 h-5" />
            <span>Create New Project</span>
            </button>
        )}

        {/* Projects List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : (
          <div className="space-y-3">
            {projects?.map((project) => (
              <div
                key={project.id}
                onClick={() => handleProjectSelect(project)}
                className="node-card cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-primary-50 text-primary-600">
                    <FolderOpen className="w-5 h-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-slate-900 group-hover:text-primary-600 transition-colors">
                      {project.name}
                    </h4>
                    {project.description && (
                      <p className="text-sm text-slate-600 mt-1 line-clamp-2">
                        {project.description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 mt-3 text-xs">
                      <span className="text-slate-500">
                        {formatDate(project.created_at)}
                      </span>

                      <div className="flex items-center gap-1">
                        {project.is_statistically_valid ? (
                          <>
                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                            <span className="text-green-600">Valid</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-500">Pending</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {showCreateForm && <CreateProjectForm onClose={() => setShowCreateForm(false)} />}
    </FloatingPanel>
  );
}