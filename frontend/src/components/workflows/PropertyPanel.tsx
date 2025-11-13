/**
 * PropertyPanel - Prawy sidebar do konfiguracji node
 *
 * Wyświetla formularz konfiguracji dla wybranego node:
 * - Podstawowe properties (label, description, group, estimated time)
 * - Type-specific panel (14 dedykowanych paneli per node type)
 * - Actions (save, delete)
 *
 * @example
 * <PropertyPanel
 *   node={selectedNode}
 *   onClose={() => setSelectedNode(null)}
 *   onUpdate={(config) => updateNodeConfig(node.id, config)}
 *   onDelete={() => deleteNode(node.id)}
 * />
 */

import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

// Import wszystkich property panels
import * as Panels from './propertyPanels';

interface PropertyPanelProps {
  node: Node;
  onClose: () => void;
  onUpdate: (config: any) => void;
  onDelete: () => void;
}

/**
 * PropertyPanel Component
 */
export function PropertyPanel({
  node,
  onClose,
  onUpdate,
  onDelete,
}: PropertyPanelProps) {
  const [basicConfig, setBasicConfig] = useState<any>({
    label: node.data.label || '',
    description: node.data.description || '',
  });

  const [typeSpecificConfig, setTypeSpecificConfig] = useState<any>(
    node.data.config || {}
  );

  // Reset config when node changes
  useEffect(() => {
    setBasicConfig({
      label: node.data.label || '',
      description: node.data.description || '',
    });
    setTypeSpecificConfig(node.data.config || {});
  }, [node]);

  const handleSave = () => {
    onUpdate({
      ...basicConfig,
      config: typeSpecificConfig,
    });
    onClose();
  };

  const handleDelete = () => {
    if (confirm('Czy na pewno chcesz usunąć ten node?')) {
      onDelete();
    }
  };

  const handleTypeSpecificUpdate = (config: any) => {
    setTypeSpecificConfig(config);
  };

  /**
   * Renderuje type-specific panel w zależności od typu node
   */
  const renderTypeSpecificPanel = () => {
    // IMPORTANT: Workflow type jest w node.data.type
    // node.type to React Flow component type ("workflowNode")
    const nodeType = node.data.type;

    switch (nodeType) {
      case 'start':
        return <Panels.StartPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'end':
        return <Panels.EndPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'goal':
        // Goal używa tylko basic properties (brak dedykowanego panelu)
        return (
          <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
            <p className="text-xs text-blue-700">
              Goal node używa tylko podstawowych właściwości (Name, Description).
            </p>
          </div>
        );
      case 'decision':
        return <Panels.DecisionPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'persona':
        return <Panels.GeneratePersonasPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'survey':
        return <Panels.CreateSurveyPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'focus-group':
        return <Panels.RunFocusGroupPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'analysis':
        return <Panels.AnalyzeResultsPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'insights':
        return <Panels.GenerateInsightsPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      // Backward compatibility - stare typy z underscore
      case 'loop_start':
        return <Panels.LoopStartPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'loop_end':
        return <Panels.LoopEndPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'create_project':
        return <Panels.CreateProjectPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'generate_personas':
        return <Panels.GeneratePersonasPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'create_survey':
        return <Panels.CreateSurveyPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'run_focus_group':
        return <Panels.RunFocusGroupPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'analyze_results':
        return <Panels.AnalyzeResultsPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'generate_insights':
        return <Panels.GenerateInsightsPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'compare_groups':
        return <Panels.CompareGroupsPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'filter_data':
        return <Panels.FilterDataPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      case 'export_report':
        return <Panels.ExportReportPanel node={node} onUpdate={handleTypeSpecificUpdate} />;
      default:
        return (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50/50 p-4">
            <p className="text-xs text-yellow-700">
              Unknown node type: <strong>{nodeType}</strong>
              <br />
              Brak dedykowanego panelu dla tego typu node.
            </p>
          </div>
        );
    }
  };

  return (
    <div className="w-80 border-l border-border bg-background overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-foreground">
            Configure Node
          </h3>
          <Badge variant="secondary" className="text-xs">
            {node.data.type}
          </Badge>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {/* Basic Properties */}
          <div>
            <Label htmlFor="node-label">Node Name</Label>
            <Input
              id="node-label"
              value={basicConfig.label}
              onChange={(e) =>
                setBasicConfig({ ...basicConfig, label: e.target.value })
              }
              className="mt-1.5"
              placeholder="Enter node name"
            />
          </div>

          <div>
            <Label htmlFor="node-description">
              Description
              <span className="text-xs text-muted-foreground ml-1">
                (opcjonalny)
              </span>
            </Label>
            <Textarea
              id="node-description"
              value={basicConfig.description}
              onChange={(e) =>
                setBasicConfig({ ...basicConfig, description: e.target.value })
              }
              className="mt-1.5"
              rows={2}
              placeholder="Describe what this node does..."
            />
          </div>

          <Separator />

          {/* Type-specific Panel */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3">
              Configuration
            </h4>
            {renderTypeSpecificPanel()}
          </div>
        </div>
      </ScrollArea>

      {/* Footer - Actions */}
      <div className="p-4 border-t border-border space-y-2">
        <Button
          onClick={handleSave}
          className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white"
        >
          Save Configuration
        </Button>
        <Button
          onClick={handleDelete}
          variant="outline"
          className="w-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Delete Node
        </Button>
        <Button onClick={onClose} variant="ghost" className="w-full">
          Cancel
        </Button>
      </div>
    </div>
  );
}
