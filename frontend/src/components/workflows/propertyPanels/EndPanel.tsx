/**
 * EndPanel - Property panel dla END node
 *
 * END node kończy wykonanie workflow.
 * Config: success_message (opcjonalny komunikat po zakończeniu)
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { EndNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface EndPanelProps {
  node: Node;
  onUpdate: (config: EndNodeConfig) => void;
}

export function EndPanel({ node, onUpdate }: EndPanelProps) {
  const [config, setConfig] = useState<EndNodeConfig>(
    (node.data.config as EndNodeConfig) || {
      success_message: 'Workflow completed successfully',
    }
  );

  const handleChange = (field: keyof EndNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="success-message">
          Success Message
          <span className="text-xs text-muted-foreground ml-1">(opcjonalny)</span>
        </Label>
        <Textarea
          id="success-message"
          value={config.success_message || ''}
          onChange={(e) => handleChange('success_message', e.target.value)}
          className="mt-1.5"
          rows={3}
          placeholder="Komunikat wyświetlany użytkownikowi po zakończeniu workflow..."
        />
        <p className="text-xs text-muted-foreground mt-1">
          Jeśli pusty, użyty zostanie domyślny komunikat.
        </p>
      </div>

      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
        <p className="text-xs text-blue-700">
          <strong>Uwaga:</strong> END node kończy wykonanie workflow. Workflow
          może mieć wiele END nodes (różne ścieżki zakończenia). Każdy END node
          nie może mieć outgoing edges.
        </p>
      </div>
    </div>
  );
}
