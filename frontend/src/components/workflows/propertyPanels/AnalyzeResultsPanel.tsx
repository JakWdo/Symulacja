/**
 * AnalyzeResultsPanel - Property panel dla ANALYZE_RESULTS node
 *
 * AI analysis wszystkich rezultatów z poprzednich nodes.
 * Config: analysis_type, input_source, prompt_template
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { AnalyzeResultsNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { BarChart3 } from 'lucide-react';

interface AnalyzeResultsPanelProps {
  node: Node;
  onUpdate: (config: AnalyzeResultsNodeConfig) => void;
}

export function AnalyzeResultsPanel({
  node,
  onUpdate,
}: AnalyzeResultsPanelProps) {
  const [config, setConfig] = useState<AnalyzeResultsNodeConfig>(
    (node.data.config as AnalyzeResultsNodeConfig) || {
      analysis_type: 'summary',
      input_source: 'focus_group',
    }
  );

  const handleChange = (field: keyof AnalyzeResultsNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const analysisDescriptions = {
    summary: 'Ogólne podsumowanie kluczowych punktów',
    sentiment: 'Analiza sentymentu (positive/neutral/negative breakdown)',
    themes: 'Ekstrakcja głównych tematów i wzorców',
    insights: 'Głębokie insights i rekomendacje biznesowe',
  };

  return (
    <div className="space-y-4">
      {/* Analysis Type */}
      <div>
        <Label htmlFor="analysis-type">
          Analysis Type <span className="text-red-500">*</span>
        </Label>
        <Select
          value={config.analysis_type}
          onValueChange={(v) =>
            handleChange(
              'analysis_type',
              v as 'summary' | 'sentiment' | 'themes' | 'insights'
            )
          }
        >
          <SelectTrigger id="analysis-type" className="mt-1.5">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="summary">
              <div>
                <div className="font-medium">Summary</div>
                <div className="text-xs text-muted-foreground">
                  {analysisDescriptions.summary}
                </div>
              </div>
            </SelectItem>
            <SelectItem value="sentiment">
              <div>
                <div className="font-medium">Sentiment Analysis</div>
                <div className="text-xs text-muted-foreground">
                  {analysisDescriptions.sentiment}
                </div>
              </div>
            </SelectItem>
            <SelectItem value="themes">
              <div>
                <div className="font-medium">Thematic Analysis</div>
                <div className="text-xs text-muted-foreground">
                  {analysisDescriptions.themes}
                </div>
              </div>
            </SelectItem>
            <SelectItem value="insights">
              <div>
                <div className="font-medium">Deep Insights</div>
                <div className="text-xs text-muted-foreground">
                  {analysisDescriptions.insights}
                </div>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-1.5">
          {analysisDescriptions[config.analysis_type]}
        </p>
      </div>

      {/* Input Source */}
      <div>
        <Label htmlFor="input-source">
          Input Source <span className="text-red-500">*</span>
        </Label>
        <Select
          value={config.input_source}
          onValueChange={(v) =>
            handleChange(
              'input_source',
              v as 'focus_group' | 'survey' | 'personas'
            )
          }
        >
          <SelectTrigger id="input-source" className="mt-1.5">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="focus_group">
              <div>
                <div className="font-medium">Focus Group</div>
                <div className="text-xs text-muted-foreground">
                  Analiza dyskusji z focus group
                </div>
              </div>
            </SelectItem>
            <SelectItem value="survey">
              <div>
                <div className="font-medium">Survey</div>
                <div className="text-xs text-muted-foreground">
                  Analiza odpowiedzi z ankiety
                </div>
              </div>
            </SelectItem>
            <SelectItem value="personas">
              <div>
                <div className="font-medium">Personas</div>
                <div className="text-xs text-muted-foreground">
                  Analiza profili person
                </div>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground mt-1.5">
          Skąd brać dane do analizy (output z poprzedniego node)
        </p>
      </div>

      {/* Custom Prompt Template */}
      <div>
        <Label htmlFor="prompt-template">
          Custom Prompt Template
          <span className="text-xs text-muted-foreground ml-1">(opcjonalny)</span>
        </Label>
        <Textarea
          id="prompt-template"
          value={config.prompt_template || ''}
          onChange={(e) => handleChange('prompt_template', e.target.value)}
          className="mt-1.5 font-mono text-sm"
          rows={5}
          placeholder="Jeśli chcesz custom prompt dla LLM, wpisz tutaj...&#10;&#10;Dostępne zmienne:&#10;- {{data}} - dane wejściowe&#10;- {{analysis_type}} - wybrany typ analizy&#10;- {{context}} - kontekst z poprzednich nodes"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Jeśli puste, użyty zostanie domyślny prompt dla wybranego typu analizy.
        </p>
      </div>

      {/* Info Badge */}
      <div className="rounded-lg border border-purple-200 bg-purple-50/50 p-4">
        <div className="flex items-start gap-2">
          <BarChart3 className="w-4 h-4 text-purple-600 mt-0.5" />
          <div className="text-xs text-purple-700">
            <p className="font-semibold mb-1">AI-Powered Analysis</p>
            <p>
              Ten node używa Google Gemini 2.5 Pro do głębokiej analizy danych.
              Wyniki zawierają strukturyzowane insights gotowe do eksportu.
            </p>
          </div>
        </div>
      </div>

      {/* Expected Output */}
      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <p className="text-xs font-medium mb-2">Expected Output:</p>
        <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
          {config.analysis_type === 'summary' && (
            <>
              <li>Executive summary (3-5 paragraphs)</li>
              <li>Key findings (bullet points)</li>
              <li>Notable quotes or data points</li>
            </>
          )}
          {config.analysis_type === 'sentiment' && (
            <>
              <li>Overall sentiment score (0-100)</li>
              <li>Breakdown: positive/neutral/negative %</li>
              <li>Sentiment drivers (top reasons)</li>
            </>
          )}
          {config.analysis_type === 'themes' && (
            <>
              <li>Main themes (3-7 themes)</li>
              <li>Theme prevalence (how often mentioned)</li>
              <li>Sub-themes and patterns</li>
            </>
          )}
          {config.analysis_type === 'insights' && (
            <>
              <li>Strategic insights (3-5 deep insights)</li>
              <li>Opportunities and risks</li>
              <li>Actionable recommendations</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
}
