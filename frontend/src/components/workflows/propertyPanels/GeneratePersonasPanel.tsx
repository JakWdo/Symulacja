/**
 * GeneratePersonasPanel - Property panel dla GENERATE_PERSONAS node
 *
 * Generuje AI personas używając PersonaOrchestrationService.
 * Config: count, demographic_preset, target_audience_description, advanced_options
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { GeneratePersonasNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, Users } from 'lucide-react';

interface GeneratePersonasPanelProps {
  node: Node;
  onUpdate: (config: GeneratePersonasNodeConfig) => void;
}

export function GeneratePersonasPanel({
  node,
  onUpdate,
}: GeneratePersonasPanelProps) {
  const [config, setConfig] = useState<GeneratePersonasNodeConfig>(
    (node.data.config as GeneratePersonasNodeConfig) || {
      count: 20,
      demographic_preset: 'poland_general',
      advanced_options: {
        diversity_level: 'medium',
        include_edge_cases: false,
      },
    }
  );

  const [advancedOpen, setAdvancedOpen] = useState(false);

  const handleChange = (field: keyof GeneratePersonasNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const handleAdvancedChange = (field: string, value: any) => {
    const updated = {
      ...config,
      advanced_options: {
        ...config.advanced_options,
        [field]: value,
      },
    };
    setConfig(updated);
    onUpdate(updated);
  };

  const estimatedTime = Math.ceil((config.count / 20) * 45); // ~45s dla 20 person

  return (
    <div className="space-y-4">
      {/* Count */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <Label htmlFor="count">
            Number of Personas <span className="text-red-500">*</span>
          </Label>
          <Badge variant="outline" className="text-xs">
            <Users className="w-3 h-3 mr-1" />
            {config.count}
          </Badge>
        </div>
        <Slider
          id="count"
          value={[config.count]}
          onValueChange={(v) => handleChange('count', v[0])}
          min={1}
          max={100}
          step={1}
          className="mb-2"
        />
        <Input
          type="number"
          value={config.count}
          onChange={(e) => handleChange('count', parseInt(e.target.value) || 1)}
          min={1}
          max={100}
          className="text-sm"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Szacowany czas: ~{estimatedTime}s
        </p>
      </div>

      {/* Demographic Preset */}
      <div>
        <Label htmlFor="preset">Demographic Preset</Label>
        <Select
          value={config.demographic_preset || 'poland_general'}
          onValueChange={(v) => handleChange('demographic_preset', v)}
        >
          <SelectTrigger id="preset" className="mt-1.5">
            <SelectValue placeholder="Wybierz preset" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="poland_general">Poland - General</SelectItem>
            <SelectItem value="poland_tech">Poland - Tech</SelectItem>
            <SelectItem value="poland_urban">Poland - Urban</SelectItem>
            <SelectItem value="poland_rural">Poland - Rural</SelectItem>
            <SelectItem value="gen_z">Gen Z (18-27)</SelectItem>
            <SelectItem value="millennials">Millennials (28-43)</SelectItem>
            <SelectItem value="gen_x">Gen X (44-59)</SelectItem>
            <SelectItem value="boomers">Boomers (60+)</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-1">
          Predefiniowane rozkłady demograficzne
        </p>
      </div>

      {/* Target Audience Description */}
      <div>
        <Label htmlFor="target-audience">
          Target Audience Description
          <span className="text-xs text-muted-foreground ml-1">(opcjonalny)</span>
        </Label>
        <Textarea
          id="target-audience"
          value={config.target_audience_description || ''}
          onChange={(e) =>
            handleChange('target_audience_description', e.target.value)
          }
          className="mt-1.5"
          rows={3}
          placeholder="Describe your target audience... (e.g., 'Tech-savvy professionals from Warsaw who use mobile banking')"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Volny opis grupy docelowej - AI dostosuje persony
        </p>
      </div>

      {/* Advanced Options */}
      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger className="flex items-center justify-between w-full p-3 rounded-figma-inner border border-border hover:bg-muted/50 transition-colors">
          <span className="text-sm font-medium">Advanced Options</span>
          <ChevronDown
            className={`w-4 h-4 transition-transform ${
              advancedOpen ? 'rotate-180' : ''
            }`}
          />
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-3 space-y-3 pl-3 border-l-2 border-border">
          {/* Diversity Level */}
          <div>
            <Label htmlFor="diversity">Diversity Level</Label>
            <Select
              value={config.advanced_options?.diversity_level || 'medium'}
              onValueChange={(v) => handleAdvancedChange('diversity_level', v)}
            >
              <SelectTrigger id="diversity" className="mt-1.5">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low - Homogeneous group</SelectItem>
                <SelectItem value="medium">Medium - Balanced mix</SelectItem>
                <SelectItem value="high">High - Very diverse</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Include Edge Cases */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="edge-cases"
              checked={config.advanced_options?.include_edge_cases || false}
              onCheckedChange={(checked) =>
                handleAdvancedChange('include_edge_cases', checked)
              }
            />
            <Label htmlFor="edge-cases" className="text-sm cursor-pointer">
              Include Edge Cases
            </Label>
          </div>
          <p className="text-xs text-muted-foreground">
            Dodaj nietypowe persony (outliers) dla szerszej perspektywy
          </p>

          {/* Urbanicity */}
          <div>
            <Label htmlFor="urbanicity">Urbanicity</Label>
            <Select
              value={config.advanced_options?.urbanicity || 'mixed'}
              onValueChange={(v) => handleAdvancedChange('urbanicity', v)}
            >
              <SelectTrigger id="urbanicity" className="mt-1.5">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="urban">Urban</SelectItem>
                <SelectItem value="suburban">Suburban</SelectItem>
                <SelectItem value="rural">Rural</SelectItem>
                <SelectItem value="mixed">Mixed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <div className="rounded-figma-inner border border-green-200 bg-green-50/50 p-4">
        <p className="text-xs text-green-700">
          <strong>Generacja person:</strong> Używa PersonaOrchestrationService z
          segmentacją demograficzną. Wyniki są walidowane statystycznie (test
          chi-kwadrat).
        </p>
      </div>
    </div>
  );
}
