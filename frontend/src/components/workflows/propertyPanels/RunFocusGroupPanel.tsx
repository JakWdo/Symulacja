/**
 * RunFocusGroupPanel - Property panel dla RUN_FOCUS_GROUP node
 *
 * Przeprowadza symulowaną grupę fokusową z AI personas.
 * Config: focus_group_title, topics, participant_ids, moderator_style, rounds
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import { RunFocusGroupNodeConfig } from '@/types/workflowNodeConfigs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, MessageSquare } from 'lucide-react';

interface RunFocusGroupPanelProps {
  node: Node;
  onUpdate: (config: RunFocusGroupNodeConfig) => void;
}

export function RunFocusGroupPanel({
  node,
  onUpdate,
}: RunFocusGroupPanelProps) {
  const [config, setConfig] = useState<RunFocusGroupNodeConfig>(
    (node.data.config as RunFocusGroupNodeConfig) || {
      focus_group_title: 'New Focus Group',
      topics: [],
      moderator_style: 'neutral',
      rounds: 3,
    }
  );

  const handleChange = (field: keyof RunFocusGroupNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const addTopic = () => {
    const updated = {
      ...config,
      topics: [...config.topics, ''],
    };
    setConfig(updated);
    onUpdate(updated);
  };

  const removeTopic = (index: number) => {
    const updated = {
      ...config,
      topics: config.topics.filter((_, i) => i !== index),
    };
    setConfig(updated);
    onUpdate(updated);
  };

  const updateTopic = (index: number, value: string) => {
    const topics = [...config.topics];
    topics[index] = value;
    const updated = { ...config, topics };
    setConfig(updated);
    onUpdate(updated);
  };

  const estimatedTime = Math.ceil(
    (config.topics.length * (config.rounds || 3) * 10) / 60
  ); // ~10s per topic per round

  return (
    <div className="space-y-4">
      {/* Focus Group Title */}
      <div>
        <Label htmlFor="fg-title">
          Focus Group Title <span className="text-red-500">*</span>
        </Label>
        <Input
          id="fg-title"
          value={config.focus_group_title}
          onChange={(e) => handleChange('focus_group_title', e.target.value)}
          className="mt-1.5"
          placeholder="e.g., Mobile App Features Discussion"
          required
        />
      </div>

      {/* Discussion Topics */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>
            Discussion Topics <span className="text-red-500">*</span>
          </Label>
          <Badge variant="secondary">
            <MessageSquare className="w-3 h-3 mr-1" />
            {config.topics.length} topic(s)
          </Badge>
        </div>

        {config.topics.length > 0 ? (
          <div className="space-y-2">
            {config.topics.map((topic, index) => (
              <div key={index} className="flex gap-2">
                <Textarea
                  value={topic}
                  onChange={(e) => updateTopic(index, e.target.value)}
                  className="flex-1"
                  rows={2}
                  placeholder={`Topic ${index + 1}: What would you like to discuss?`}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeTopic(index)}
                  className="h-auto text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 border-2 border-dashed border-border rounded-lg">
            <p className="text-sm text-muted-foreground">
              Brak tematów. Dodaj przynajmniej jeden temat dyskusji.
            </p>
          </div>
        )}

        <Button
          onClick={addTopic}
          variant="outline"
          className="w-full"
          size="sm"
          disabled={config.topics.length >= 10}
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Topic
        </Button>
        <p className="text-xs text-muted-foreground">
          Limit: 1-10 topics. Więcej tematów = dłuższa dyskusja.
        </p>
      </div>

      {/* Moderator Style */}
      <div>
        <Label htmlFor="moderator-style">Moderator Style</Label>
        <Select
          value={config.moderator_style || 'neutral'}
          onValueChange={(v) =>
            handleChange(
              'moderator_style',
              v as 'neutral' | 'probing' | 'directive'
            )
          }
        >
          <SelectTrigger id="moderator-style" className="mt-1.5">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="neutral">
              <div>
                <div className="font-medium">Neutral</div>
                <div className="text-xs text-muted-foreground">
                  Facilituje bez wpływania na odpowiedzi
                </div>
              </div>
            </SelectItem>
            <SelectItem value="probing">
              <div>
                <div className="font-medium">Probing</div>
                <div className="text-xs text-muted-foreground">
                  Zadaje follow-up questions dla głębszych insights
                </div>
              </div>
            </SelectItem>
            <SelectItem value="directive">
              <div>
                <div className="font-medium">Directive</div>
                <div className="text-xs text-muted-foreground">
                  Kieruje dyskusją w konkretnym kierunku
                </div>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Rounds */}
      <div>
        <Label htmlFor="rounds">Discussion Rounds</Label>
        <Input
          id="rounds"
          type="number"
          value={config.rounds}
          onChange={(e) => handleChange('rounds', parseInt(e.target.value) || 1)}
          className="mt-1.5"
          min={1}
          max={5}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Liczba rund dyskusji dla każdego tematu (1-5)
        </p>
      </div>

      {/* Participant IDs (optional) */}
      <div>
        <Label htmlFor="participants">
          Participant IDs
          <span className="text-xs text-muted-foreground ml-1">(opcjonalny)</span>
        </Label>
        <Textarea
          id="participants"
          value={
            config.participant_ids ? config.participant_ids.join('\n') : ''
          }
          onChange={(e) => {
            const ids = e.target.value
              .split('\n')
              .filter((id) => id.trim())
              .map((id) => id.trim());
            handleChange('participant_ids', ids.length > 0 ? ids : undefined);
          }}
          className="mt-1.5 font-mono text-xs"
          rows={3}
          placeholder="Pozostaw puste aby użyć person z poprzedniego node&#10;&#10;Lub podaj UUID person (jeden per linia):&#10;uuid-1&#10;uuid-2&#10;uuid-3"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Jeśli puste, użyte zostaną persony z poprzedniego node (Generate
          Personas)
        </p>
      </div>

      {/* Estimated Time */}
      <div className="rounded-lg border border-green-200 bg-green-50/50 p-4">
        <p className="text-xs text-green-700">
          <strong>Szacowany czas wykonania:</strong> ~{estimatedTime} min
          <br />
          <strong>Model:</strong> Używa asynchronicznych wywołań LLM dla
          realistycznej dynamiki dyskusji
        </p>
      </div>
    </div>
  );
}
