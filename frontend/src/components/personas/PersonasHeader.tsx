import React from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Database } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { useTranslation } from 'react-i18next';
import type { Project } from '@/types';

interface PersonasHeaderProps {
  selectedProject: Project | null;
  projects: Project[];
  projectsLoading: boolean;
  onProjectChange: (projectId: string) => void;
  onGenerateClick: () => void;
  onRagDocumentsClick: () => void;
}

export function PersonasHeader({
  selectedProject,
  projects,
  projectsLoading,
  onProjectChange,
  onGenerateClick,
  onRagDocumentsClick,
}: PersonasHeaderProps) {
  const { t } = useTranslation('personas');

  return (
    <PageHeader
      title={t('page.title')}
      subtitle={t('page.subtitle')}
      actions={
        <>
          <Button
            type="button"
            variant="outline"
            className="border-border text-card-foreground"
            onClick={onRagDocumentsClick}
          >
            <Database className="w-4 h-4 mr-2" />
            {t('page.ragDocumentsButton')}
          </Button>
          <Select
            value={selectedProject?.id || ''}
            onValueChange={onProjectChange}
          >
            <SelectTrigger className="bg-muted border-0 rounded-md px-3.5 py-2 h-9 hover:bg-muted/80 transition-colors">
              <SelectValue
                placeholder={t('page.selectProjectPlaceholder')}
                className="font-['Crimson_Text',_serif] text-[14px] text-foreground leading-5"
              />
            </SelectTrigger>
            <SelectContent className="bg-muted border-border">
              {projectsLoading ? (
                <div className="flex items-center justify-center p-2">
                  <SpinnerLogo className="w-4 h-4" />
                </div>
              ) : projects.length === 0 ? (
                <div className="p-2 text-sm text-muted-foreground">{t('page.noProjectsFound')}</div>
              ) : (
                projects.map((project) => (
                  <SelectItem
                    key={project.id}
                    value={project.id}
                    className="font-['Crimson_Text',_serif] text-[14px] text-foreground focus:bg-accent"
                  >
                    {project.name}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
          <Button
            onClick={onGenerateClick}
            className="bg-brand hover:bg-brand/90 text-brand-foreground"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('page.generateButton')}
          </Button>
        </>
      }
    />
  );
}
