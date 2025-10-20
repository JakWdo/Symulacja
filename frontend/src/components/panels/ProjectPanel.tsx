import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FloatingPanel } from '@/components/ui/FloatingPanel';
import { projectsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { Plus, FolderOpen, CheckCircle2, XCircle } from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/button'; // Import Button
import type { Project } from '@/types';
import { Logo } from '@/components/ui/Logo';

// Komponent formularza do tworzenia projektu
function CreateProjectForm({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const queryClient = useQueryClient();

  const createProjectMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setName('');
      setDescription('');
      onClose(); // Zamknij formularz po sukcesie
    },
    onError: (error: Error) => {
      alert(`Error creating project: ${error.message}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Project name is required.');
      return;
    }
    // Domyślna demografia z większą różnorodnością
    const defaultDemographics = {
      age_group: {
        '18-24': 0.18,
        '25-34': 0.26,
        '35-44': 0.22,
        '45-54': 0.18,
        '55+': 0.16,
      },
      gender: {
        female: 0.5,
        male: 0.45,
        non_binary: 0.05,
      },
      education_level: {
        high_school: 0.25,
        bachelors: 0.32,
        masters: 0.22,
        phd: 0.07,
        vocational: 0.14,
      },
      income_bracket: {
        '<30k': 0.18,
        '30k-60k': 0.28,
        '60k-100k': 0.27,
        '100k+': 0.27,
      },
      location: {
        urban: 0.45,
        suburban: 0.33,
        rural: 0.18,
        remote: 0.04,
      },
    };

    createProjectMutation.mutate({
      name: name.trim(),
      description: description.trim() || null,
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
          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={createProjectMutation.isPending}
          >
            Create
          </Button>
        </div>
      </form>
    </div>
  );
}


export function ProjectPanel() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const activePanel = useAppStore(state => state.activePanel);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const selectedProject = useAppStore(state => state.selectedProject);
  const setSelectedProject = useAppStore(state => state.setSelectedProject);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data: projects = [], isLoading, isError, error } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  });

  useEffect(() => {
    if (selectedProject && !projects.find((project) => project.id === selectedProject.id)) {
      setSelectedProject(null);
    }
  }, [projects, selectedProject, setSelectedProject]);

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    setActivePanel(null);
  };

  const sortedProjects = useMemo(
    () =>
      [...projects].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [projects],
  );

  return (
    <FloatingPanel
      isOpen={activePanel === 'projects'}
      onClose={() => setActivePanel(null)}
      title="Projects"
      panelKey="projects"
      size="lg"
    >
      <div className="p-4 space-y-4">
        {/* Create Button */}
        {!showCreateForm && (
          <Button
            onClick={() => setShowCreateForm(true)}
            variant="secondary"
            className="w-full flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>Create New Project</span>
          </Button>
        )}

        {/* Projects List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Logo className="w-8 h-8" spinning />
          </div>
        ) : isError ? (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
            {error instanceof Error ? error.message : 'Unable to load projects.'}
          </div>
        ) : (
          <div className="space-y-3">
            {sortedProjects.map((project) => {
              const isSelected = selectedProject?.id === project.id;
              return (
                <div
                  key={project.id}
                  onClick={() => handleProjectSelect(project)}
                className={cn(
                  'node-card cursor-pointer group transition-colors border-2',
                  isSelected
                    ? 'border-primary-200 shadow-lg bg-white'
                    : 'border-transparent hover:border-primary-100',
                )}
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
              );
            })}
          </div>
        )}
      </div>
      {showCreateForm && <CreateProjectForm onClose={() => setShowCreateForm(false)} />}
    </FloatingPanel>
  );
}
