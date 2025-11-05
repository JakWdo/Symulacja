/**
 * StartPanel - Property panel dla START node
 *
 * START node jest entry point workflow.
 * MVP: Tylko manual trigger (user kliknie "Run Workflow").
 *
 * Config: Minimalna - tylko trigger_type (zawsze "manual")
 */

import { Node } from 'reactflow';
import { StartNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

interface StartPanelProps {
  node: Node;
  onUpdate: (config: StartNodeConfig) => void;
}

export function StartPanel({ node, onUpdate }: StartPanelProps) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const config = (node.data.config || {
    trigger_type: 'manual',
  }) as StartNodeConfig;

  // StartPanel nie ma edytowalnych pól - onUpdate nie jest używany
  // ale musimy go przyjąć dla consistent interface
  void onUpdate;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-muted/50 p-4">
        <div className="flex items-center gap-2 mb-2">
          <Label className="text-sm font-medium">Trigger Type</Label>
          <Badge variant="secondary">Manual</Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          Ten workflow jest uruchamiany ręcznie przez użytkownika (przycisk "Run
          Workflow").
        </p>
      </div>

      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
        <p className="text-xs text-blue-700">
          <strong>Uwaga:</strong> START node jest entry point workflow. Każdy
          workflow musi mieć dokładnie jeden START node bez incoming edges.
        </p>
      </div>
    </div>
  );
}
