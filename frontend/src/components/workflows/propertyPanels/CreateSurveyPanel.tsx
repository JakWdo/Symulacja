/**
 * CreateSurveyPanel - Property panel dla CREATE_SURVEY node
 *
 * Tworzy ankietę z manual questions lub AI-generated.
 * Config: survey_name, questions, ai_generate_questions, ai_prompt, target_personas
 */

import { useState } from 'react';
import { Node } from 'reactflow';
import {
  CreateSurveyNodeConfig,
  SurveyQuestion,
} from '@/types/workflowNodeConfigs';
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
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, Sparkles } from 'lucide-react';

interface CreateSurveyPanelProps {
  node: Node;
  onUpdate: (config: CreateSurveyNodeConfig) => void;
}

export function CreateSurveyPanel({ node, onUpdate }: CreateSurveyPanelProps) {
  const [config, setConfig] = useState<CreateSurveyNodeConfig>(
    (node.data.config as CreateSurveyNodeConfig) || {
      survey_name: 'New Survey',
      questions: [],
      ai_generate_questions: false,
      target_personas: 'all',
    }
  );

  const handleChange = (field: keyof CreateSurveyNodeConfig, value: any) => {
    const updated = { ...config, [field]: value };
    setConfig(updated);
    onUpdate(updated);
  };

  const addQuestion = () => {
    const newQuestion: SurveyQuestion = {
      text: '',
      type: 'single',
      required: true,
    };
    const updated = {
      ...config,
      questions: [...(config.questions || []), newQuestion],
    };
    setConfig(updated);
    onUpdate(updated);
  };

  const removeQuestion = (index: number) => {
    const updated = {
      ...config,
      questions: config.questions?.filter((_, i) => i !== index) || [],
    };
    setConfig(updated);
    onUpdate(updated);
  };

  const updateQuestion = (index: number, field: keyof SurveyQuestion, value: any) => {
    const questions = [...(config.questions || [])];
    questions[index] = { ...questions[index], [field]: value };
    const updated = { ...config, questions };
    setConfig(updated);
    onUpdate(updated);
  };

  const updateQuestionOptions = (index: number, optionsText: string) => {
    const options = optionsText.split('\n').filter((o) => o.trim());
    updateQuestion(index, 'options', options);
  };

  return (
    <div className="space-y-4">
      {/* Survey Name */}
      <div>
        <Label htmlFor="survey-name">
          Survey Name <span className="text-red-500">*</span>
        </Label>
        <Input
          id="survey-name"
          value={config.survey_name}
          onChange={(e) => handleChange('survey_name', e.target.value)}
          className="mt-1.5"
          placeholder="e.g., Customer Satisfaction Survey"
          required
        />
      </div>

      {/* Survey Description */}
      <div>
        <Label htmlFor="survey-description">
          Description
          <span className="text-xs text-muted-foreground ml-1">(opcjonalny)</span>
        </Label>
        <Textarea
          id="survey-description"
          value={config.survey_description || ''}
          onChange={(e) => handleChange('survey_description', e.target.value)}
          className="mt-1.5"
          rows={2}
          placeholder="Brief description of the survey purpose..."
        />
      </div>

      {/* AI Generation Toggle */}
      <div className="flex items-start space-x-3 rounded-figma-inner border border-purple-200 bg-purple-50/50 p-3">
        <Checkbox
          id="ai-generate"
          checked={config.ai_generate_questions || false}
          onCheckedChange={(checked) =>
            handleChange('ai_generate_questions', checked)
          }
        />
        <div className="flex-1">
          <Label htmlFor="ai-generate" className="cursor-pointer flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-purple-600" />
            AI-Generate Questions
          </Label>
          <p className="text-xs text-muted-foreground mt-0.5">
            Pozwól AI wygenerować pytania na podstawie promptu
          </p>
        </div>
      </div>

      {/* AI Prompt (jeśli AI enabled) */}
      {config.ai_generate_questions && (
        <div>
          <Label htmlFor="ai-prompt">
            AI Prompt <span className="text-red-500">*</span>
          </Label>
          <Textarea
            id="ai-prompt"
            value={config.ai_prompt || ''}
            onChange={(e) => handleChange('ai_prompt', e.target.value)}
            className="mt-1.5"
            rows={4}
            placeholder="Describe what you want to learn... (e.g., 'Create 5 questions about mobile app usage patterns and satisfaction')"
            required={config.ai_generate_questions}
          />
        </div>
      )}

      {/* Manual Questions (jeśli AI disabled) */}
      {!config.ai_generate_questions && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Questions</Label>
            <Badge variant="secondary">
              {config.questions?.length || 0} pytań
            </Badge>
          </div>

          {config.questions && config.questions.length > 0 ? (
            <div className="space-y-3">
              {config.questions.map((question, index) => (
                <div
                  key={index}
                  className="p-3 border border-border rounded-figma-inner space-y-2 relative"
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeQuestion(index)}
                    className="absolute top-2 right-2 h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>

                  <div>
                    <Label className="text-xs">Question Text</Label>
                    <Input
                      value={question.text}
                      onChange={(e) =>
                        updateQuestion(index, 'text', e.target.value)
                      }
                      className="mt-1"
                      placeholder="Enter question..."
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs">Type</Label>
                      <Select
                        value={question.type}
                        onValueChange={(v) => updateQuestion(index, 'type', v)}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="single">Single Choice</SelectItem>
                          <SelectItem value="multiple">Multiple Choice</SelectItem>
                          <SelectItem value="text">Text</SelectItem>
                          <SelectItem value="scale">Scale</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-end">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={`required-${index}`}
                          checked={question.required || false}
                          onCheckedChange={(checked) =>
                            updateQuestion(index, 'required', checked)
                          }
                        />
                        <Label
                          htmlFor={`required-${index}`}
                          className="text-xs cursor-pointer"
                        >
                          Required
                        </Label>
                      </div>
                    </div>
                  </div>

                  {/* Options dla single/multiple choice */}
                  {(question.type === 'single' ||
                    question.type === 'multiple') && (
                    <div>
                      <Label className="text-xs">
                        Options (jedna opcja per linia)
                      </Label>
                      <Textarea
                        value={question.options?.join('\n') || ''}
                        onChange={(e) =>
                          updateQuestionOptions(index, e.target.value)
                        }
                        className="mt-1 font-mono text-xs"
                        rows={3}
                        placeholder="Option 1&#10;Option 2&#10;Option 3"
                      />
                    </div>
                  )}

                  {/* Scale range dla scale type */}
                  {question.type === 'scale' && (
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Label className="text-xs">Min</Label>
                        <Input
                          type="number"
                          value={question.scale_min || 1}
                          onChange={(e) =>
                            updateQuestion(
                              index,
                              'scale_min',
                              parseInt(e.target.value)
                            )
                          }
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Max</Label>
                        <Input
                          type="number"
                          value={question.scale_max || 5}
                          onChange={(e) =>
                            updateQuestion(
                              index,
                              'scale_max',
                              parseInt(e.target.value)
                            )
                          }
                          className="mt-1"
                        />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 border-2 border-dashed border-border rounded-figma-inner">
              <p className="text-sm text-muted-foreground">
                Brak pytań. Kliknij "Add Question" aby dodać pierwsze pytanie.
              </p>
            </div>
          )}

          <Button
            onClick={addQuestion}
            variant="outline"
            className="w-full"
            size="sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Question
          </Button>
        </div>
      )}

      {/* Target Personas */}
      <div>
        <Label htmlFor="target-personas">Target Personas</Label>
        <Input
          id="target-personas"
          value={config.target_personas || 'all'}
          onChange={(e) => handleChange('target_personas', e.target.value)}
          className="mt-1.5"
          placeholder="all"
        />
        <p className="text-xs text-muted-foreground mt-1">
          "all" lub filter expression (np. "age &gt; 30")
        </p>
      </div>
    </div>
  );
}
