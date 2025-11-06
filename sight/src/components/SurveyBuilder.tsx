import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Switch } from './ui/switch';
import { ArrowLeft, Plus, GripVertical, Trash2, RadioIcon as RadioButton, CheckSquare, BarChart3, FileText, Play, TrendingUp, Grid3x3, List, GitBranch, Sparkles } from 'lucide-react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface SurveyBuilderProps {
  onBack: () => void;
  onSave: (survey: any) => void;
}

interface SkipLogic {
  enabled: boolean;
  targetQuestionId?: string;
  condition?: string;
  value?: string;
}

interface Question {
  id: string;
  type: 'single-choice' | 'multiple-choice' | 'rating-scale' | 'open-text' | 'nps' | 'matrix' | 'ranking';
  title: string;
  description?: string;
  options?: string[];
  required: boolean;
  scaleMin?: number;
  scaleMax?: number;
  matrixRows?: string[];
  matrixColumns?: string[];
  skipLogic?: SkipLogic;
}

const questionTypes = [
  {
    id: 'single-choice',
    label: 'Single Choice',
    icon: RadioButton,
    description: 'Radio buttons - one answer'
  },
  {
    id: 'multiple-choice', 
    label: 'Multiple Choice',
    icon: CheckSquare,
    description: 'Checkboxes - multiple answers'
  },
  {
    id: 'rating-scale',
    label: 'Rating Scale',
    icon: BarChart3,
    description: '1-5 or 1-10 point scale'
  },
  {
    id: 'nps',
    label: 'NPS',
    icon: TrendingUp,
    description: 'Net Promoter Score 0-10',
    advanced: true
  },
  {
    id: 'matrix',
    label: 'Matrix',
    icon: Grid3x3,
    description: 'Multiple questions, same scale',
    advanced: true
  },
  {
    id: 'ranking',
    label: 'Ranking',
    icon: List,
    description: 'Rank options by preference',
    advanced: true
  },
  {
    id: 'open-text',
    label: 'Open Text',
    icon: FileText,
    description: 'Free text response'
  }
];

const mockProjects = [
  { id: 1, name: "Mobile App Launch Research" },
  { id: 2, name: "Product Development Study" },
  { id: 3, name: "Marketing Research" }
];

// Sortable Question Item Component
function SortableQuestionItem({ 
  question, 
  updateQuestion, 
  deleteQuestion, 
  addOption, 
  updateOption, 
  removeOption,
  addMatrixRow,
  updateMatrixRow,
  removeMatrixRow,
  addMatrixColumn,
  updateMatrixColumn,
  removeMatrixColumn,
  getQuestionIcon,
  allQuestions
}: any) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: question.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const Icon = getQuestionIcon(question.type);
  const questionTypeMeta = questionTypes.find(qt => qt.id === question.type);

  return (
    <div ref={setNodeRef} style={style}>
      <Card className="bg-card border border-border">
        <CardHeader className="pb-3">
          <div className="flex items-start gap-3">
            <button
              className="cursor-grab active:cursor-grabbing mt-1 text-muted-foreground hover:text-foreground"
              {...attributes}
              {...listeners}
            >
              <GripVertical className="w-5 h-5" />
            </button>
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4 text-brand-orange" />
                <Badge variant="outline" className="text-xs">
                  {questionTypeMeta?.label}
                </Badge>
                {questionTypeMeta?.advanced && (
                  <Badge variant="outline" className="text-xs bg-brand-gold/10 text-brand-gold border-brand-gold/30">
                    <Sparkles className="w-3 h-3 mr-1" />
                    Advanced
                  </Badge>
                )}
              </div>
              <Input
                placeholder="Question title"
                value={question.title}
                onChange={(e) => updateQuestion(question.id, { title: e.target.value })}
                className="text-base"
              />
              <Input
                placeholder="Description (optional)"
                value={question.description || ''}
                onChange={(e) => updateQuestion(question.id, { description: e.target.value })}
                className="text-sm"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => deleteQuestion(question.id)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Single/Multiple Choice Options */}
          {(question.type === 'single-choice' || question.type === 'multiple-choice') && (
            <div className="space-y-2">
              <Label className="text-sm text-muted-foreground">Options</Label>
              {question.options?.map((option: string, index: number) => (
                <div key={index} className="flex items-center gap-2">
                  <Input
                    value={option}
                    onChange={(e) => updateOption(question.id, index, e.target.value)}
                    placeholder={`Option ${index + 1}`}
                  />
                  {question.options && question.options.length > 2 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeOption(question.id, index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => addOption(question.id)}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Option
              </Button>
            </div>
          )}

          {/* Rating Scale */}
          {question.type === 'rating-scale' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Minimum</Label>
                <Input
                  type="number"
                  value={question.scaleMin}
                  onChange={(e) => updateQuestion(question.id, { scaleMin: parseInt(e.target.value) })}
                />
              </div>
              <div>
                <Label>Maximum</Label>
                <Input
                  type="number"
                  value={question.scaleMax}
                  onChange={(e) => updateQuestion(question.id, { scaleMax: parseInt(e.target.value) })}
                />
              </div>
            </div>
          )}

          {/* NPS Question */}
          {question.type === 'nps' && (
            <div className="p-4 border border-border rounded-lg bg-muted/30 space-y-2">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <TrendingUp className="w-4 h-4 text-brand-orange" />
                <span>Net Promoter Score (0-10 scale)</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Automatically categorizes responses: 0-6 (Detractors), 7-8 (Passives), 9-10 (Promoters)
              </p>
              <div className="flex gap-1 mt-2">
                {[0,1,2,3,4,5,6,7,8,9,10].map(num => (
                  <div 
                    key={num} 
                    className={`flex-1 h-8 flex items-center justify-center text-xs border border-border rounded ${
                      num <= 6 ? 'bg-red-50 dark:bg-red-950/20' : 
                      num <= 8 ? 'bg-yellow-50 dark:bg-yellow-950/20' : 
                      'bg-green-50 dark:bg-green-950/20'
                    }`}
                  >
                    {num}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Matrix Question */}
          {question.type === 'matrix' && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Rows (Questions)</Label>
                {question.matrixRows?.map((row: string, index: number) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      value={row}
                      onChange={(e) => updateMatrixRow(question.id, index, e.target.value)}
                      placeholder={`Row ${index + 1}`}
                    />
                    {question.matrixRows && question.matrixRows.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeMatrixRow(question.id, index)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => addMatrixRow(question.id)}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Row
                </Button>
              </div>

              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Columns (Scale)</Label>
                {question.matrixColumns?.map((col: string, index: number) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      value={col}
                      onChange={(e) => updateMatrixColumn(question.id, index, e.target.value)}
                      placeholder={`Column ${index + 1}`}
                    />
                    {question.matrixColumns && question.matrixColumns.length > 2 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeMatrixColumn(question.id, index)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => addMatrixColumn(question.id)}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Column
                </Button>
              </div>
            </div>
          )}

          {/* Ranking Question */}
          {question.type === 'ranking' && (
            <div className="space-y-2">
              <Label className="text-sm text-muted-foreground">Items to Rank</Label>
              {question.options?.map((option: string, index: number) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="flex items-center justify-center w-6 h-6 text-xs border border-border rounded bg-muted">
                    {index + 1}
                  </div>
                  <Input
                    value={option}
                    onChange={(e) => updateOption(question.id, index, e.target.value)}
                    placeholder={`Item ${index + 1}`}
                  />
                  {question.options && question.options.length > 2 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeOption(question.id, index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => addOption(question.id)}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Item
              </Button>
              <p className="text-xs text-muted-foreground">
                Respondents will drag and drop these items to rank them
              </p>
            </div>
          )}

          {/* Skip Logic */}
          <div className="pt-4 border-t border-border space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-brand-orange" />
                <Label className="text-sm">Skip Logic</Label>
              </div>
              <Switch 
                checked={question.skipLogic?.enabled || false}
                onCheckedChange={(checked) => updateQuestion(question.id, { 
                  skipLogic: { ...question.skipLogic, enabled: checked }
                })}
              />
            </div>
            
            {question.skipLogic?.enabled && (
              <div className="space-y-3 pl-6">
                <div>
                  <Label className="text-xs">If answer is</Label>
                  <Select 
                    value={question.skipLogic?.value}
                    onValueChange={(value) => updateQuestion(question.id, {
                      skipLogic: { ...question.skipLogic, value }
                    })}
                  >
                    <SelectTrigger className="text-sm">
                      <SelectValue placeholder="Select condition" />
                    </SelectTrigger>
                    <SelectContent>
                      {question.options?.map((opt, idx) => (
                        <SelectItem key={idx} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label className="text-xs">Then skip to</Label>
                  <Select 
                    value={question.skipLogic?.targetQuestionId}
                    onValueChange={(value) => updateQuestion(question.id, {
                      skipLogic: { ...question.skipLogic, targetQuestionId: value }
                    })}
                  >
                    <SelectTrigger className="text-sm">
                      <SelectValue placeholder="Select question" />
                    </SelectTrigger>
                    <SelectContent>
                      {allQuestions
                        .filter((q: Question) => q.id !== question.id)
                        .map((q: Question) => (
                          <SelectItem key={q.id} value={q.id}>
                            {q.title || 'Untitled question'}
                          </SelectItem>
                        ))
                      }
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>

          {/* Required Checkbox */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id={`required-${question.id}`}
              checked={question.required}
              onChange={(e) => updateQuestion(question.id, { required: e.target.checked })}
              className="rounded"
            />
            <Label htmlFor={`required-${question.id}`} className="text-sm cursor-pointer">
              Required question
            </Label>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function SurveyBuilder({ onBack, onSave }: SurveyBuilderProps) {
  const [surveyTitle, setSurveyTitle] = useState('');
  const [surveyDescription, setSurveyDescription] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [sampleSize, setSampleSize] = useState('1000');
  const [questions, setQuestions] = useState<Question[]>([]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const addQuestion = (type: Question['type']) => {
    const newQuestion: Question = {
      id: `question-${Date.now()}`,
      type,
      title: '',
      required: false,
      ...(type === 'single-choice' || type === 'multiple-choice' ? { options: ['Option 1', 'Option 2'] } : {}),
      ...(type === 'ranking' ? { options: ['Item 1', 'Item 2', 'Item 3'] } : {}),
      ...(type === 'rating-scale' ? { scaleMin: 1, scaleMax: 5 } : {}),
      ...(type === 'matrix' ? { 
        matrixRows: ['Question 1', 'Question 2'], 
        matrixColumns: ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] 
      } : {}),
      skipLogic: { enabled: false }
    };
    setQuestions([...questions, newQuestion]);
  };

  const updateQuestion = (id: string, updates: Partial<Question>) => {
    setQuestions(questions.map(q => q.id === id ? { ...q, ...updates } : q));
  };

  const deleteQuestion = (id: string) => {
    setQuestions(questions.filter(q => q.id !== id));
  };

  const addOption = (questionId: string) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.options) {
      updateQuestion(questionId, {
        options: [...question.options, `${question.type === 'ranking' ? 'Item' : 'Option'} ${question.options.length + 1}`]
      });
    }
  };

  const updateOption = (questionId: string, optionIndex: number, value: string) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.options) {
      const newOptions = [...question.options];
      newOptions[optionIndex] = value;
      updateQuestion(questionId, { options: newOptions });
    }
  };

  const removeOption = (questionId: string, optionIndex: number) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.options && question.options.length > 2) {
      const newOptions = question.options.filter((_, index) => index !== optionIndex);
      updateQuestion(questionId, { options: newOptions });
    }
  };

  const addMatrixRow = (questionId: string) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.matrixRows) {
      updateQuestion(questionId, {
        matrixRows: [...question.matrixRows, `Question ${question.matrixRows.length + 1}`]
      });
    }
  };

  const updateMatrixRow = (questionId: string, rowIndex: number, value: string) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.matrixRows) {
      const newRows = [...question.matrixRows];
      newRows[rowIndex] = value;
      updateQuestion(questionId, { matrixRows: newRows });
    }
  };

  const removeMatrixRow = (questionId: string, rowIndex: number) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.matrixRows && question.matrixRows.length > 1) {
      const newRows = question.matrixRows.filter((_, index) => index !== rowIndex);
      updateQuestion(questionId, { matrixRows: newRows });
    }
  };

  const addMatrixColumn = (questionId: string) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.matrixColumns) {
      updateQuestion(questionId, {
        matrixColumns: [...question.matrixColumns, `Column ${question.matrixColumns.length + 1}`]
      });
    }
  };

  const updateMatrixColumn = (questionId: string, colIndex: number, value: string) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.matrixColumns) {
      const newColumns = [...question.matrixColumns];
      newColumns[colIndex] = value;
      updateQuestion(questionId, { matrixColumns: newColumns });
    }
  };

  const removeMatrixColumn = (questionId: string, colIndex: number) => {
    const question = questions.find(q => q.id === questionId);
    if (question && question.matrixColumns && question.matrixColumns.length > 2) {
      const newColumns = question.matrixColumns.filter((_, index) => index !== colIndex);
      updateQuestion(questionId, { matrixColumns: newColumns });
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setQuestions((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleSave = () => {
    const survey = {
      title: surveyTitle,
      description: surveyDescription,
      projectId: selectedProject,
      sampleSize: parseInt(sampleSize),
      questions,
      status: 'draft'
    };
    onSave(survey);
  };

  const getQuestionIcon = (type: string) => {
    const questionType = questionTypes.find(qt => qt.id === type);
    return questionType?.icon || FileText;
  };

  const advancedQuestionTypes = questionTypes.filter(qt => qt.advanced);
  const basicQuestionTypes = questionTypes.filter(qt => !qt.advanced);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Surveys
        </Button>
        <div className="flex-1">
          <h1 className="text-foreground mb-2">Survey Builder</h1>
          <p className="text-muted-foreground">Create a new synthetic survey</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleSave}>
            Save Draft
          </Button>
          <Button 
            onClick={handleSave}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            <Play className="w-4 h-4 mr-2" />
            Launch Survey
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Sidebar - Question Types */}
        <div className="col-span-3 space-y-4">
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm">Basic Questions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {basicQuestionTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.id}
                    onClick={() => addQuestion(type.id as Question['type'])}
                    className="w-full p-3 border border-border rounded-lg hover:border-brand-orange hover:bg-brand-orange/5 transition-colors text-left"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-brand-orange" />
                      <span className="text-sm text-foreground">{type.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{type.description}</p>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-gold" />
                Advanced Questions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {advancedQuestionTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.id}
                    onClick={() => addQuestion(type.id as Question['type'])}
                    className="w-full p-3 border border-brand-gold/30 bg-brand-gold/5 rounded-lg hover:border-brand-gold hover:bg-brand-gold/10 transition-colors text-left"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-brand-gold" />
                      <span className="text-sm text-foreground">{type.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{type.description}</p>
                  </button>
                );
              })}
            </CardContent>
          </Card>

          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm">Survey Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <Label className="text-xs">Sample Size</Label>
                <Input
                  type="number"
                  value={sampleSize}
                  onChange={(e) => setSampleSize(e.target.value)}
                  placeholder="1000"
                />
              </div>
              <div>
                <Label className="text-xs">Response Time</Label>
                <Select defaultValue="5-10">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5-10">5-10 minutes</SelectItem>
                    <SelectItem value="10-15">10-15 minutes</SelectItem>
                    <SelectItem value="15-20">15-20 minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content - Survey Builder */}
        <div className="col-span-9 space-y-6">
          {/* Survey Details */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground">Survey Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Survey Title</Label>
                <Input
                  value={surveyTitle}
                  onChange={(e) => setSurveyTitle(e.target.value)}
                  placeholder="e.g., Customer Satisfaction Survey"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={surveyDescription}
                  onChange={(e) => setSurveyDescription(e.target.value)}
                  placeholder="Brief description of your survey goals"
                  rows={3}
                />
              </div>
              <div>
                <Label>Project</Label>
                <Select value={selectedProject} onValueChange={setSelectedProject}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {mockProjects.map((project) => (
                      <SelectItem key={project.id} value={project.id.toString()}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Questions Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-foreground">Questions ({questions.length})</h2>
              {questions.some(q => q.skipLogic?.enabled) && (
                <Badge variant="outline" className="gap-1">
                  <GitBranch className="w-3 h-3" />
                  Skip Logic Active
                </Badge>
              )}
            </div>

            {questions.length === 0 ? (
              <Card className="bg-card border border-dashed border-border">
                <CardContent className="p-12 text-center">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-foreground mb-2">No questions yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Click on a question type on the left to add it to your survey
                  </p>
                </CardContent>
              </Card>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={questions.map(q => q.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-4">
                    {questions.map((question) => (
                      <SortableQuestionItem
                        key={question.id}
                        question={question}
                        updateQuestion={updateQuestion}
                        deleteQuestion={deleteQuestion}
                        addOption={addOption}
                        updateOption={updateOption}
                        removeOption={removeOption}
                        addMatrixRow={addMatrixRow}
                        updateMatrixRow={updateMatrixRow}
                        removeMatrixRow={removeMatrixRow}
                        addMatrixColumn={addMatrixColumn}
                        updateMatrixColumn={updateMatrixColumn}
                        removeMatrixColumn={removeMatrixColumn}
                        getQuestionIcon={getQuestionIcon}
                        allQuestions={questions}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
