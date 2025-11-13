/**
 * DecisionPanel - Property panel dla DECISION node
 *
 * DECISION node ewaluuje condition i wybiera branch (true/false).
 * Config: condition (Python expression), true_branch_label, false_branch_label
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { DecisionNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Info } from 'lucide-react';

interface DecisionPanelProps {
  node: Node;
  onUpdate: (config: DecisionNodeConfig) => void;
}

export function DecisionPanel({ node, onUpdate }: DecisionPanelProps) {
  const [config, setConfig] = useState<DecisionNodeConfig>(
    (node.data.config as DecisionNodeConfig) || {
      condition: 'true',
      true_branch_label: 'Yes',
      false_branch_label: 'No',
    }
  );

  const handleChange = (field: keyof DecisionNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="condition">
          Condition <span className="text-red-500">*</span>
        </Label>
        <Textarea
          id="condition"
          value={config.condition}
          onChange={(e) => handleChange('condition', e.target.value)}
          className="mt-1.5 font-mono text-sm"
          rows={3}
          placeholder="e.g., persona_count > 10"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          Python expression. Dostępne zmienne: persona_count, survey_nps_score,
          sentiment, etc.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="true-label">True Branch Label</Label>
          <Input
            id="true-label"
            value={config.true_branch_label || 'Yes'}
            onChange={(e) => handleChange('true_branch_label', e.target.value)}
            className="mt-1.5"
            placeholder="Yes"
          />
        </div>

        <div>
          <Label htmlFor="false-label">False Branch Label</Label>
          <Input
            id="false-label"
            value={config.false_branch_label || 'No'}
            onChange={(e) => handleChange('false_branch_label', e.target.value)}
            className="mt-1.5"
            placeholder="No"
          />
        </div>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription className="text-xs">
          <strong>Dozwolone operatory:</strong> ==, !=, &lt;, &gt;, &lt;=, &gt;=,
          and, or, not
          <br />
          <strong>Zabronione:</strong> import, exec, eval, open, file
        </AlertDescription>
      </Alert>

      <div className="rounded-figma-inner border border-blue-200 bg-blue-50/50 p-4">
        <p className="text-xs text-blue-700">
          <strong>Przykłady:</strong>
          <br />• len(personas) &gt; 10
          <br />• survey_nps_score &gt;= 7
          <br />• sentiment['positive'] &gt; 60
        </p>
      </div>
    </div>
  );
}
