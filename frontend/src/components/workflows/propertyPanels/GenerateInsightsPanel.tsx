/**
 * GenerateInsightsPanel - Property panel dla GENERATE_INSIGHTS node
 *
 * Generuje głębokie insights z analizy danych.
 * Config: insight_focus, output_format, include_quotes
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { GenerateInsightsNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Lightbulb, CheckSquare } from 'lucide-react';

interface GenerateInsightsPanelProps {
  node: Node;
  onUpdate: (config: GenerateInsightsNodeConfig) => void;
}

export function GenerateInsightsPanel({
  node,
  onUpdate,
}: GenerateInsightsPanelProps) {
  const [config, setConfig] = useState<GenerateInsightsNodeConfig>(
    (node.data.config as GenerateInsightsNodeConfig) || {
      insight_focus: ['pain_points', 'opportunities'],
      output_format: 'summary',
      include_quotes: true,
    }
  );

  const handleChange = (field: keyof GenerateInsightsNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const toggleInsightFocus = (focus: string) => {
    const current = config.insight_focus || [];
    const updated = current.includes(focus)
      ? current.filter((f) => f !== focus)
      : [...current, focus];
    handleChange('insight_focus', updated);
  };

  const insightFocusOptions = [
    { value: 'pain_points', label: 'Pain Points', description: 'Problemy i frustracje użytkowników' },
    { value: 'opportunities', label: 'Opportunities', description: 'Szanse i niezaspokojone potrzeby' },
    { value: 'trends', label: 'Trends', description: 'Wzorce i trendy w danych' },
    { value: 'behaviors', label: 'Behaviors', description: 'Kluczowe zachowania użytkowników' },
    { value: 'motivations', label: 'Motivations', description: 'Motywacje i drivers' },
    { value: 'barriers', label: 'Barriers', description: 'Bariery i przeszkody' },
  ];

  return (
    <div className="space-y-4">
      {/* Insight Focus (multi-select via checkboxes) */}
      <div>
        <Label className="mb-3 block">
          Insight Focus <span className="text-red-500">*</span>
        </Label>
        <div className="space-y-2">
          {insightFocusOptions.map((option) => (
            <div
              key={option.value}
              className="flex items-start space-x-3 p-3 rounded-figma-inner border border-border hover:bg-muted/50 transition-colors"
            >
              <Checkbox
                id={option.value}
                checked={config.insight_focus?.includes(option.value) || false}
                onCheckedChange={() => toggleInsightFocus(option.value)}
              />
              <div className="flex-1">
                <Label
                  htmlFor={option.value}
                  className="cursor-pointer font-medium"
                >
                  {option.label}
                </Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {option.description}
                </p>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-2">
          <CheckSquare className="w-4 h-4 text-muted-foreground" />
          <p className="text-xs text-muted-foreground">
            Wybrano: {config.insight_focus?.length || 0} obszarów
          </p>
        </div>
      </div>

      {/* Output Format */}
      <div>
        <Label htmlFor="output-format">
          Output Format <span className="text-red-500">*</span>
        </Label>
        <Select
          value={config.output_format}
          onValueChange={(v) =>
            handleChange(
              'output_format',
              v as 'summary' | 'detailed' | 'bullet_points'
            )
          }
        >
          <SelectTrigger id="output-format" className="mt-1.5">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="summary">
              <div>
                <div className="font-medium">Summary</div>
                <div className="text-xs text-muted-foreground">
                  Zwięzłe podsumowanie (2-3 paragrafy per insight)
                </div>
              </div>
            </SelectItem>
            <SelectItem value="detailed">
              <div>
                <div className="font-medium">Detailed</div>
                <div className="text-xs text-muted-foreground">
                  Szczegółowa analiza z przykładami
                </div>
              </div>
            </SelectItem>
            <SelectItem value="bullet_points">
              <div>
                <div className="font-medium">Bullet Points</div>
                <div className="text-xs text-muted-foreground">
                  Listowe punkty - łatwe do skanowania
                </div>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Include Quotes */}
      <div className="flex items-start space-x-3 p-3 rounded-figma-inner border border-border bg-muted/30">
        <Checkbox
          id="include-quotes"
          checked={config.include_quotes || false}
          onCheckedChange={(checked) => handleChange('include_quotes', checked)}
        />
        <div className="flex-1">
          <Label htmlFor="include-quotes" className="cursor-pointer font-medium">
            Include Quotes
          </Label>
          <p className="text-xs text-muted-foreground mt-0.5">
            Dodaj cytaty z person/focus groups jako supporting evidence dla
            insights
          </p>
        </div>
      </div>

      {/* Info */}
      <div className="rounded-figma-inner border border-yellow-200 bg-yellow-50/50 p-4">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-4 h-4 text-yellow-600 mt-0.5" />
          <div className="text-xs text-yellow-700">
            <p className="font-semibold mb-1">Deep Insight Generation</p>
            <p>
              Ten node używa zaawansowanych technik analizy AI aby ekstrapolować
              głębokie insights z danych. Im więcej obszarów focus wybierzesz,
              tym bogatsze będą wyniki.
            </p>
          </div>
        </div>
      </div>

      {/* Expected Output Preview */}
      <div className="rounded-figma-inner border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Expected Output Structure:</p>
        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
          <li>Insight per focus area (np. 3-5 insights dla pain_points)</li>
          <li>
            Format: {config.output_format === 'summary' && 'Paragraphs'}
            {config.output_format === 'detailed' && 'Extended analysis'}
            {config.output_format === 'bullet_points' && 'Concise bullet list'}
          </li>
          {config.include_quotes && <li>Supporting quotes from data</li>}
          <li>Actionable recommendations</li>
        </ul>
      </div>
    </div>
  );
}
