import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { ArrowLeft, Plus, GripVertical, Trash2, RadioIcon as RadioButton, CheckSquare, BarChart3, FileText, Play, Settings } from 'lucide-react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

interface SurveyBuilderProps {
  onBack: () => void;
  onSave: (survey: any) => void;
}

interface Question {
  id: string;
  type: 'single-choice' | 'multiple-choice' | 'rating-scale' | 'open-text';
  title: string;
  description?: string;
  options?: string[];
  required: boolean;
  scaleMin?: number;
  scaleMax?: number;
}

const questionTypes = [
  {
    id: 'single-choice',
    label: 'Single Choice',
    icon: RadioButton,
    description: 'Radio buttons - one answer only'
  },
  {
    id: 'multiple-choice', 
    label: 'Multiple Choice',
    icon: CheckSquare,
    description: 'Checkboxes - multiple answers allowed'
  },
  {
    id: 'rating-scale',
    label: 'Rating Scale',
    icon: BarChart3,
    description: '1-5 or 1-10 point scale'
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

export function SurveyBuilder({ onBack, onSave }: SurveyBuilderProps) {
  const [surveyTitle, setSurveyTitle] = useState('');
  const [surveyDescription, setSurveyDescription] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [sampleSize, setSampleSize] = useState('1000');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [draggedQuestionType, setDraggedQuestionType] = useState<string | null>(null);

  const addQuestion = (type: Question['type']) => {
    const newQuestion: Question = {
      id: `question-${Date.now()}`,
      type,
      title: '',
      required: false,
      ...(type === 'single-choice' || type === 'multiple-choice' ? { options: ['Option 1', 'Option 2'] } : {}),
      ...(type === 'rating-scale' ? { scaleMin: 1, scaleMax: 5 } : {})
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
        options: [...question.options, `Option ${question.options.length + 1}`]
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

  const onDragEnd = (result: any) => {
    if (!result.destination) return;

    if (result.source.droppableId === 'question-types' && result.destination.droppableId === 'survey-questions') {
      // Adding a new question
      const questionType = questionTypes[result.source.index];
      addQuestion(questionType.id as Question['type']);
    } else if (result.source.droppableId === 'survey-questions' && result.destination.droppableId === 'survey-questions') {
      // Reordering questions
      const items = Array.from(questions);
      const [reorderedItem] = items.splice(result.source.index, 1);
      items.splice(result.destination.index, 0, reorderedItem);
      setQuestions(items);
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

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Surveys
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl brand-orange">Survey Builder</h1>
            <p className="text-muted-foreground">Create a new synthetic survey</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleSave} disabled={!surveyTitle || !selectedProject || questions.length === 0}>
              Save Draft
            </Button>
            <Button 
              onClick={handleSave}
              disabled={!surveyTitle || !selectedProject || questions.length === 0}
              className="bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              <Play className="w-4 h-4 mr-2" />
              Launch Survey
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Question Types Palette */}
          <div className="lg:col-span-1">
            <Card className="bg-card border border-border sticky top-6">
              <CardHeader>
                <CardTitle className="text-card-foreground flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Question Types
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Droppable droppableId="question-types" isDropDisabled={true}>
                  {(provided) => (
                    <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-2">
                      {questionTypes.map((type, index) => (
                        <Draggable key={type.id} draggableId={type.id} index={index}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className={`p-3 rounded-lg border border-border bg-muted/30 cursor-grab active:cursor-grabbing hover:bg-muted/50 transition-colors ${
                                snapshot.isDragging ? 'shadow-lg bg-card' : ''
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <type.icon className="w-5 h-5 brand-orange flex-shrink-0 mt-0.5" />
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm text-card-foreground">{type.label}</p>
                                  <p className="text-xs text-muted-foreground">{type.description}</p>
                                </div>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
                <Separator className="my-4" />
                <div className="space-y-2 text-xs text-muted-foreground">
                  <p>Drag question types to the survey area to add them</p>
                  <p>Reorder questions by dragging them up or down</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Survey Builder */}
          <div className="lg:col-span-3 space-y-6">
            {/* Survey Configuration */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-card-foreground">Survey Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Survey Title</Label>
                    <Input
                      id="title"
                      value={surveyTitle}
                      onChange={(e) => setSurveyTitle(e.target.value)}
                      placeholder="e.g., Product Feature Preferences"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="project">Associated Project</Label>
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
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea
                    id="description"
                    value={surveyDescription}
                    onChange={(e) => setSurveyDescription(e.target.value)}
                    placeholder="Brief description of what this survey aims to discover"
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sampleSize">Sample Size</Label>
                  <Select value={sampleSize} onValueChange={setSampleSize}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="500">500 responses</SelectItem>
                      <SelectItem value="1000">1,000 responses</SelectItem>
                      <SelectItem value="2500">2,500 responses</SelectItem>
                      <SelectItem value="5000">5,000 responses</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Survey Questions */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-card-foreground flex items-center justify-between">
                  Survey Questions
                  <Badge variant="outline">
                    {questions.length} question{questions.length !== 1 ? 's' : ''}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Droppable droppableId="survey-questions">
                  {(provided, snapshot) => (
                    <div
                      {...provided.droppableProps}
                      ref={provided.innerRef}
                      className={`space-y-4 min-h-[200px] ${
                        snapshot.isDraggingOver ? 'bg-muted/20 rounded-lg' : ''
                      }`}
                    >
                      {questions.length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                          <BarChart3 className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                          <p>Drag question types from the left panel to start building your survey</p>
                        </div>
                      )}
                      
                      {questions.map((question, index) => (
                        <Draggable key={question.id} draggableId={question.id} index={index}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              className={`bg-muted/30 border border-border rounded-lg p-4 ${
                                snapshot.isDragging ? 'shadow-lg bg-card' : ''
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <div {...provided.dragHandleProps} className="mt-2">
                                  <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
                                </div>
                                
                                <div className="flex-1 space-y-3">
                                  <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-2">
                                      {(() => {
                                        const Icon = getQuestionIcon(question.type);
                                        return <Icon className="w-4 h-4 brand-orange" />;
                                      })()}
                                      <Badge variant="outline" className="text-xs">
                                        {questionTypes.find(qt => qt.id === question.type)?.label}
                                      </Badge>
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
                                  
                                  <div className="space-y-2">
                                    <Input
                                      value={question.title}
                                      onChange={(e) => updateQuestion(question.id, { title: e.target.value })}
                                      placeholder="Enter your question..."
                                      className="bg-background"
                                    />
                                    
                                    {(question.type === 'single-choice' || question.type === 'multiple-choice') && (
                                      <div className="space-y-2">
                                        {question.options?.map((option, optionIndex) => (
                                          <div key={optionIndex} className="flex items-center gap-2">
                                            <div className="w-4 flex justify-center">
                                              {question.type === 'single-choice' ? (
                                                <div className="w-3 h-3 rounded-full border border-border" />
                                              ) : (
                                                <div className="w-3 h-3 border border-border" />
                                              )}
                                            </div>
                                            <Input
                                              value={option}
                                              onChange={(e) => updateOption(question.id, optionIndex, e.target.value)}
                                              className="bg-background"
                                            />
                                            {question.options && question.options.length > 2 && (
                                              <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => removeOption(question.id, optionIndex)}
                                                className="text-destructive hover:text-destructive"
                                              >
                                                <Trash2 className="w-4 h-4" />
                                              </Button>
                                            )}
                                          </div>
                                        ))}
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => addOption(question.id)}
                                          className="text-primary hover:text-primary"
                                        >
                                          <Plus className="w-4 h-4 mr-2" />
                                          Add Option
                                        </Button>
                                      </div>
                                    )}
                                    
                                    {question.type === 'rating-scale' && (
                                      <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2">
                                          <Label>Scale:</Label>
                                          <Select
                                            value={question.scaleMin?.toString()}
                                            onValueChange={(value) => updateQuestion(question.id, { scaleMin: parseInt(value) })}
                                          >
                                            <SelectTrigger className="w-20">
                                              <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                              <SelectItem value="1">1</SelectItem>
                                            </SelectContent>
                                          </Select>
                                          <span>to</span>
                                          <Select
                                            value={question.scaleMax?.toString()}
                                            onValueChange={(value) => updateQuestion(question.id, { scaleMax: parseInt(value) })}
                                          >
                                            <SelectTrigger className="w-20">
                                              <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                              <SelectItem value="5">5</SelectItem>
                                              <SelectItem value="10">10</SelectItem>
                                            </SelectContent>
                                          </Select>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DragDropContext>
  );
}