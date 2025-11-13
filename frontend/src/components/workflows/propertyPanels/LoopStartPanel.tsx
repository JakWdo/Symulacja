/**
 * LoopStartPanel - Property panel dla LOOP_START node
 *
 * Rozpoczyna iterację przez array (np. każda persona osobno).
 * Config: iteration_variable, items_source, max_iterations
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { LoopStartNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RotateCw, AlertTriangle } from 'lucide-react';

interface LoopStartPanelProps {
  node: Node;
  onUpdate: (config: LoopStartNodeConfig) => void;
}

export function LoopStartPanel({ node, onUpdate }: LoopStartPanelProps) {
  const [config, setConfig] = useState<LoopStartNodeConfig>(
    (node.data.config as LoopStartNodeConfig) || {
      iteration_variable: 'item',
      items_source: 'items',
      max_iterations: 100,
    }
  );

  const handleChange = (field: keyof LoopStartNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-4">
      {/* Iteration Variable */}
      <div>
        <Label htmlFor="iteration-var">
          Iteration Variable <span className="text-red-500">*</span>
        </Label>
        <Input
          id="iteration-var"
          value={config.iteration_variable}
          onChange={(e) => handleChange('iteration_variable', e.target.value)}
          className="mt-1.5 font-mono"
          placeholder="e.g., persona, item, response"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          Nazwa zmiennej dla bieżącego elementu iteracji (dostępna w nodes wewnątrz
          loop)
        </p>
      </div>

      {/* Items Source */}
      <div>
        <Label htmlFor="items-source">
          Items Source <span className="text-red-500">*</span>
        </Label>
        <Input
          id="items-source"
          value={config.items_source}
          onChange={(e) => handleChange('items_source', e.target.value)}
          className="mt-1.5 font-mono"
          placeholder="e.g., personas, survey_responses"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          Zmienna zawierająca array do iteracji (output z poprzedniego node)
        </p>
      </div>

      {/* Max Iterations */}
      <div>
        <Label htmlFor="max-iterations">Max Iterations</Label>
        <Input
          id="max-iterations"
          type="number"
          value={config.max_iterations}
          onChange={(e) =>
            handleChange('max_iterations', parseInt(e.target.value) || 100)
          }
          className="mt-1.5"
          min={1}
          max={1000}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Safety limit - maximum liczba iteracji (default: 100)
        </p>
      </div>

      {/* Loop Example */}
      <div className="rounded-figma-inner border border-blue-200 bg-blue-50/50 p-4">
        <div className="flex items-start gap-2">
          <RotateCw className="w-4 h-4 text-blue-600 mt-0.5" />
          <div className="text-xs text-blue-700">
            <p className="font-semibold mb-1">Przykład Loop:</p>
            <p className="font-mono bg-blue-100 p-2 rounded mt-1">
              for {config.iteration_variable} in {config.items_source}:
              <br />
              &nbsp;&nbsp;# Wykonaj nodes między LOOP_START a LOOP_END
              <br />
              &nbsp;&nbsp;# {config.iteration_variable} jest dostępny jako zmienna
            </p>
          </div>
        </div>
      </div>

      {/* Warning */}
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription className="text-xs">
          <strong>Uwaga:</strong> Loop musi być zamknięty odpowiadającym LOOP_END
          node. Upewnij się że:
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            <li>LOOP_END node ma ustawiony prawidłowy loop_start_node_id</li>
            <li>Loop nie tworzy nieskończonej pętli</li>
            <li>Liczba iteracji nie przekracza max_iterations</li>
          </ul>
        </AlertDescription>
      </Alert>

      {/* Use Cases */}
      <div className="rounded-figma-inner border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Common Use Cases:</p>
        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
          <li>Iteracja przez każdą personę (individual processing)</li>
          <li>Batch processing survey responses</li>
          <li>Wykonanie tego samego workflow dla każdej grupy</li>
          <li>Conditional per-item actions</li>
        </ul>
      </div>
    </div>
  );
}
