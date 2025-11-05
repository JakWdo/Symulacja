/**
 * CompareGroupsPanel - Property panel dla COMPARE_GROUPS node
 *
 * Porównuje dwie grupy danych (np. dwie kohort person).
 * Config: group_a_source, group_b_source, comparison_metrics
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { CompareGroupsNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { GitCompare, CheckSquare } from 'lucide-react';

interface CompareGroupsPanelProps {
  node: Node;
  onUpdate: (config: CompareGroupsNodeConfig) => void;
}

export function CompareGroupsPanel({ node, onUpdate }: CompareGroupsPanelProps) {
  const [config, setConfig] = useState<CompareGroupsNodeConfig>(
    (node.data.config as CompareGroupsNodeConfig) || {
      group_a_source: '',
      group_b_source: '',
      comparison_metrics: [],
    }
  );

  const handleChange = (field: keyof CompareGroupsNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const handleMetricsChange = (text: string) => {
    const metrics = text
      .split('\n')
      .filter((m) => m.trim())
      .map((m) => m.trim());
    handleChange('comparison_metrics', metrics);
  };

  const suggestedMetrics = [
    'age_distribution',
    'gender_balance',
    'sentiment_avg',
    'engagement_level',
    'satisfaction_score',
    'response_rate',
  ];

  return (
    <div className="space-y-4">
      {/* Group A Source */}
      <div>
        <Label htmlFor="group-a">
          Group A Source <span className="text-red-500">*</span>
        </Label>
        <Input
          id="group-a"
          value={config.group_a_source}
          onChange={(e) => handleChange('group_a_source', e.target.value)}
          className="mt-1.5"
          placeholder="Node ID grupy A (np. 'generate-personas-1')"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          ID node z pierwszą grupą do porównania
        </p>
      </div>

      {/* Group B Source */}
      <div>
        <Label htmlFor="group-b">
          Group B Source <span className="text-red-500">*</span>
        </Label>
        <Input
          id="group-b"
          value={config.group_b_source}
          onChange={(e) => handleChange('group_b_source', e.target.value)}
          className="mt-1.5"
          placeholder="Node ID grupy B (np. 'filter-data-1')"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          ID node z drugą grupą do porównania
        </p>
      </div>

      {/* Comparison Metrics */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <Label htmlFor="metrics">
            Comparison Metrics <span className="text-red-500">*</span>
          </Label>
          <Badge variant="secondary">
            <CheckSquare className="w-3 h-3 mr-1" />
            {config.comparison_metrics.length} metric(s)
          </Badge>
        </div>
        <Textarea
          id="metrics"
          value={config.comparison_metrics.join('\n')}
          onChange={(e) => handleMetricsChange(e.target.value)}
          className="mt-1.5 font-mono text-sm"
          rows={5}
          placeholder="Jedna metryka per linia:&#10;age_distribution&#10;gender_balance&#10;sentiment_avg"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          Pola do porównania (muszą istnieć w obu grupach)
        </p>
      </div>

      {/* Suggested Metrics */}
      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Suggested Metrics:</p>
        <div className="flex flex-wrap gap-1.5">
          {suggestedMetrics.map((metric) => (
            <Badge
              key={metric}
              variant="outline"
              className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-xs"
              onClick={() => {
                const current = config.comparison_metrics;
                if (!current.includes(metric)) {
                  handleChange('comparison_metrics', [...current, metric]);
                }
              }}
            >
              + {metric}
            </Badge>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Kliknij aby dodać do comparison metrics
        </p>
      </div>

      {/* Info */}
      <div className="rounded-lg border border-purple-200 bg-purple-50/50 p-4">
        <div className="flex items-start gap-2">
          <GitCompare className="w-4 h-4 text-purple-600 mt-0.5" />
          <div className="text-xs text-purple-700">
            <p className="font-semibold mb-1">Group Comparison</p>
            <p>
              Ten node porównuje dwie grupy danych używając statystycznych metod
              (t-test, chi-square, effect size). Wyniki zawierają:
            </p>
            <ul className="list-disc list-inside mt-1 space-y-0.5">
              <li>Różnice w metrykach między grupami</li>
              <li>Statystyczna istotność różnic</li>
              <li>Visualizations (tables, charts)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Expected Output */}
      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Expected Output:</p>
        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
          <li>Comparison summary (text description)</li>
          <li>Metric-by-metric breakdown</li>
          <li>Statistical significance (p-values)</li>
          <li>Effect sizes (Cohen's d, etc.)</li>
          <li>Recommendations based on differences</li>
        </ul>
      </div>
    </div>
  );
}
