/**
 * CreateProjectPanel - Property panel dla CREATE_PROJECT node
 *
 * Tworzy nowy projekt badawczy jako kontener dla person, surveys, focus groups.
 * Config: project_name, project_description, target_demographics
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { CreateProjectNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { ChevronDown, FolderOpen } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface CreateProjectPanelProps {
  node: Node;
  onUpdate: (config: CreateProjectNodeConfig) => void;
}

export function CreateProjectPanel({ node, onUpdate }: CreateProjectPanelProps) {
  const [config, setConfig] = useState<CreateProjectNodeConfig>(
    (node.data.config as CreateProjectNodeConfig) || {
      project_name: 'New Project',
    }
  );

  const [demographicsOpen, setDemographicsOpen] = useState(false);

  const handleChange = (field: keyof CreateProjectNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const handleDemographicChange = (field: string, value: any) => {
    const updated = {
      ...config,
      target_demographics: {
        ...config.target_demographics,
        [field]: value,
      },
    };
    setConfig(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-4">
      {/* Project Name */}
      <div>
        <Label htmlFor="project-name">
          Project Name <span className="text-red-500">*</span>
        </Label>
        <Input
          id="project-name"
          value={config.project_name}
          onChange={(e) => handleChange('project_name', e.target.value)}
          className="mt-1.5"
          placeholder="e.g., Mobile App User Research Q1 2025"
          required
        />
      </div>

      {/* Project Description */}
      <div>
        <Label htmlFor="project-description">
          Description
          <span className="text-xs text-muted-foreground ml-1">(opcjonalny)</span>
        </Label>
        <Textarea
          id="project-description"
          value={config.project_description || ''}
          onChange={(e) => handleChange('project_description', e.target.value)}
          className="mt-1.5"
          rows={3}
          placeholder="Describe the research goals and context..."
        />
      </div>

      {/* Target Demographics (collapsible) */}
      <Collapsible open={demographicsOpen} onOpenChange={setDemographicsOpen}>
        <CollapsibleTrigger className="flex items-center justify-between w-full p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Target Demographics</span>
            <Badge variant="outline" className="text-xs">
              Opcjonalny
            </Badge>
          </div>
          <ChevronDown
            className={`w-4 h-4 transition-transform ${
              demographicsOpen ? 'rotate-180' : ''
            }`}
          />
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-3 space-y-3 pl-3 border-l-2 border-border">
          <p className="text-xs text-muted-foreground">
            Ustaw docelową demografię projektu. Jeśli puste, użyte zostaną defaults
            dla Polski.
          </p>

          {/* Age Range */}
          <div>
            <Label className="text-sm">Age Range</Label>
            <div className="grid grid-cols-2 gap-2 mt-1.5">
              <div>
                <Label htmlFor="age-min" className="text-xs">
                  Min
                </Label>
                <Input
                  id="age-min"
                  type="number"
                  value={config.target_demographics?.age_min || ''}
                  onChange={(e) =>
                    handleDemographicChange('age_min', parseInt(e.target.value))
                  }
                  className="mt-1"
                  placeholder="18"
                  min={0}
                  max={120}
                />
              </div>
              <div>
                <Label htmlFor="age-max" className="text-xs">
                  Max
                </Label>
                <Input
                  id="age-max"
                  type="number"
                  value={config.target_demographics?.age_max || ''}
                  onChange={(e) =>
                    handleDemographicChange('age_max', parseInt(e.target.value))
                  }
                  className="mt-1"
                  placeholder="65"
                  min={0}
                  max={120}
                />
              </div>
            </div>
          </div>

          {/* Gender */}
          <div>
            <Label htmlFor="gender" className="text-sm">
              Gender
            </Label>
            <Input
              id="gender"
              value={config.target_demographics?.gender?.join(', ') || ''}
              onChange={(e) =>
                handleDemographicChange(
                  'gender',
                  e.target.value.split(',').map((g) => g.trim())
                )
              }
              className="mt-1.5"
              placeholder="male, female, non-binary"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Rozdziel przecinkami: male, female, non-binary
            </p>
          </div>

          {/* Location */}
          <div>
            <Label htmlFor="location" className="text-sm">
              Location
            </Label>
            <Textarea
              id="location"
              value={config.target_demographics?.location?.join('\n') || ''}
              onChange={(e) =>
                handleDemographicChange(
                  'location',
                  e.target.value
                    .split('\n')
                    .filter((l) => l.trim())
                    .map((l) => l.trim())
                )
              }
              className="mt-1.5"
              rows={3}
              placeholder="Warszawa&#10;Kraków&#10;Wrocław"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Jedna lokalizacja per linia
            </p>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
        <div className="flex items-start gap-2">
          <FolderOpen className="w-4 h-4 text-blue-600 mt-0.5" />
          <p className="text-xs text-blue-700">
            Ten node tworzy nowy projekt w systemie. Projekt służy jako kontener
            dla wszystkich danych workflow (persony, surveys, focus groups).
          </p>
        </div>
      </div>
    </div>
  );
}
