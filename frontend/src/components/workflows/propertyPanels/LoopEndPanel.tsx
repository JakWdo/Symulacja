/**
 * LoopEndPanel - Property panel dla LOOP_END node
 *
 * Kończy iterację loop - wraca do LOOP_START dla następnego elementu.
 * Config: loop_start_node_id
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { LoopEndNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RotateCcw, Info } from 'lucide-react';

interface LoopEndPanelProps {
  node: Node;
  onUpdate: (config: LoopEndNodeConfig) => void;
}

export function LoopEndPanel({ node, onUpdate }: LoopEndPanelProps) {
  const [config, setConfig] = useState<LoopEndNodeConfig>(
    (node.data.config as LoopEndNodeConfig) || {
      loop_start_node_id: '',
    }
  );

  const handleChange = (field: keyof LoopEndNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-4">
      {/* Loop Start Node ID */}
      <div>
        <Label htmlFor="loop-start-id">
          Loop Start Node ID <span className="text-red-500">*</span>
        </Label>
        <Input
          id="loop-start-id"
          value={config.loop_start_node_id}
          onChange={(e) => handleChange('loop_start_node_id', e.target.value)}
          className="mt-1.5 font-mono"
          placeholder="e.g., loop-start-1"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          ID odpowiadającego LOOP_START node (musi istnieć w workflow)
        </p>
      </div>

      {/* Info Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription className="text-xs">
          <strong>Jak to działa:</strong>
          <br />
          LOOP_END node zamyka iterację rozpoczętą przez LOOP_START. Po wykonaniu
          wszystkich nodes między LOOP_START a LOOP_END, workflow wraca do
          LOOP_START dla następnego elementu.
        </AlertDescription>
      </Alert>

      {/* Visual Representation */}
      <div className="rounded-lg border border-purple-200 bg-purple-50/50 p-4">
        <div className="flex items-start gap-2">
          <RotateCcw className="w-4 h-4 text-purple-600 mt-0.5" />
          <div className="text-xs text-purple-700">
            <p className="font-semibold mb-1">Loop Flow:</p>
            <div className="font-mono bg-purple-100 p-2 rounded mt-1 space-y-1">
              <div>[LOOP_START] → iterate through items</div>
              <div>&nbsp;&nbsp;↓</div>
              <div>&nbsp;&nbsp;[Node 1] → process current item</div>
              <div>&nbsp;&nbsp;↓</div>
              <div>&nbsp;&nbsp;[Node 2] → more processing</div>
              <div>&nbsp;&nbsp;↓</div>
              <div>&nbsp;&nbsp;[LOOP_END] → go back to LOOP_START</div>
              <div>&nbsp;&nbsp;&nbsp;&nbsp;(repeat until all items processed)</div>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Rules */}
      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Validation Rules:</p>
        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
          <li>loop_start_node_id musi wskazywać na istniejący LOOP_START node</li>
          <li>LOOP_END nie może być przed LOOP_START w workflow</li>
          <li>Loop nie może być zagnieżdżony (MVP limitation)</li>
          <li>LOOP_END musi być osiągalny z LOOP_START</li>
        </ul>
      </div>

      {/* Output Info */}
      <div className="rounded-lg border border-green-200 bg-green-50/50 p-4">
        <p className="text-xs text-green-700">
          <strong>Output:</strong> Po zakończeniu loop, LOOP_END node zbiera wyniki
          wszystkich iteracji i przekazuje je do następnego node jako array.
        </p>
      </div>
    </div>
  );
}
