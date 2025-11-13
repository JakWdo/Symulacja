/**
 * FilterDataPanel - Property panel dla FILTER_DATA node
 *
 * Filtruje dane według warunków (Python expression).
 * Config: filter_expression, data_source
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { FilterDataNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Filter, Info } from 'lucide-react';

interface FilterDataPanelProps {
  node: Node;
  onUpdate: (config: FilterDataNodeConfig) => void;
}

export function FilterDataPanel({ node, onUpdate }: FilterDataPanelProps) {
  const [config, setConfig] = useState<FilterDataNodeConfig>(
    (node.data.config as FilterDataNodeConfig) || {
      filter_expression: 'true',
      data_source: '',
    }
  );

  const handleChange = (field: keyof FilterDataNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  return (
    <div className="space-y-4">
      {/* Filter Expression */}
      <div>
        <Label htmlFor="filter-expression">
          Filter Expression <span className="text-red-500">*</span>
        </Label>
        <Textarea
          id="filter-expression"
          value={config.filter_expression}
          onChange={(e) => handleChange('filter_expression', e.target.value)}
          className="mt-1.5 font-mono text-sm"
          rows={4}
          placeholder="e.g., age > 30 and gender == 'female'"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          Python expression. Dostępne pola zależą od data_source (np. age, gender,
          sentiment_score, etc.)
        </p>
      </div>

      {/* Data Source */}
      <div>
        <Label htmlFor="data-source">
          Data Source <span className="text-red-500">*</span>
        </Label>
        <Input
          id="data-source"
          value={config.data_source}
          onChange={(e) => handleChange('data_source', e.target.value)}
          className="mt-1.5"
          placeholder="Node ID (np. 'generate-personas-1')"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          ID node z którego pobierać dane do filtrowania
        </p>
      </div>

      {/* Expression Help */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription className="text-xs">
          <strong>Dozwolone operatory:</strong> ==, !=, &lt;, &gt;, &lt;=, &gt;=,
          and, or, not, in
          <br />
          <strong>Zabronione:</strong> import, exec, eval, open, file
        </AlertDescription>
      </Alert>

      {/* Examples */}
      <div className="rounded-figma-inner border border-blue-200 bg-blue-50/50 p-4">
        <p className="text-xs text-blue-700 font-semibold mb-2">
          <Filter className="inline w-3.5 h-3.5 mr-1" />
          Przykłady Filter Expressions:
        </p>
        <ul className="text-xs text-blue-700 space-y-1 list-disc list-inside">
          <li>age &gt; 30 and age &lt; 50</li>
          <li>gender == 'female' and location in ['Warszawa', 'Kraków']</li>
          <li>sentiment_score &gt;= 0.7</li>
          <li>occupation == 'Engineer' or occupation == 'Designer'</li>
          <li>has_children == True and income &gt; 5000</li>
        </ul>
      </div>

      {/* Expected Output */}
      <div className="rounded-figma-inner border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Expected Output:</p>
        <p className="text-xs text-muted-foreground">
          Przefiltrowana lista items z data_source które spełniają filter
          expression. Output można użyć w kolejnych nodes.
        </p>
      </div>

      {/* Warning */}
      <div className="rounded-figma-inner border border-yellow-200 bg-yellow-50/50 p-4">
        <p className="text-xs text-yellow-700">
          <strong>Uwaga:</strong> Filter jest wykonywany podczas runtime workflow.
          Upewnij się że pola w expression istnieją w data_source, inaczej node
          zwróci błąd.
        </p>
      </div>
    </div>
  );
}
