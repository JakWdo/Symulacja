import { useCallback } from 'react';
import { projectsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { toast } from 'sonner';

/**
 * Hook that converts backend dashboard redirect URLs into in-app navigation.
 * Falls back gracefully to dashboard view when an URL cannot be handled.
 */
export function useDashboardNavigation(onNavigate?: (view: string) => void) {
  const setSelectedProject = useAppStore((state) => state.setSelectedProject);
  const setActivePanel = useAppStore((state) => state.setActivePanel);
  const triggerProjectCreation = useAppStore((state) => state.triggerProjectCreation);

  return useCallback(
    async (url: string | undefined | null) => {
      if (!url) {
        onNavigate?.('dashboard');
        return;
      }

      // Strip origin if present and drop query/hash
      let path: string;
      try {
        const parsed = new URL(url, window.location.origin);
        path = parsed.pathname;
      } catch {
        path = url;
      }

      const segments = path
        .split('/')
        .map((segment) => segment.trim())
        .filter(Boolean);

      if (segments.length === 0) {
        onNavigate?.('dashboard');
        return;
      }

      if (segments[0] !== 'projects') {
        onNavigate?.('dashboard');
        return;
      }

      // /projects or /projects/create -> open projects list / panel
      const possibleProjectId = segments[1];
      if (!possibleProjectId) {
        onNavigate?.('projects');
        return;
      }

      if (possibleProjectId === 'create') {
        setActivePanel('projects');
        triggerProjectCreation();
        onNavigate?.('projects');
        return;
      }

      const projectId = possibleProjectId;

      try {
        const project = await projectsApi.get(projectId);
        setSelectedProject(project);

        // Handle specific sub-routes
        const action = segments[2];
        switch (action) {
          case 'personas':
            onNavigate?.('personas');
            break;
          case 'focus-groups':
            onNavigate?.('focus-group-builder');
            break;
          case 'insights':
            onNavigate?.('project-detail');
            setActivePanel('analysis');
            break;
          default:
            onNavigate?.('project-detail');
            break;
        }
      } catch (error) {
        console.error('Failed to navigate to project dashboard URL:', error);
        toast.error('Unable to open project. Please try again.');
        onNavigate?.('projects');
      }
    },
    [onNavigate, setSelectedProject, setActivePanel, triggerProjectCreation]
  );
}
