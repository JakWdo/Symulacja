import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { ArrowLeft, Plus, GripVertical, Trash2, RadioIcon as RadioButton, CheckSquare, BarChart3, FileText, Settings } from 'lucide-react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { surveysApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import type { Question } from '@/types';
import { toast } from '@/components/ui/toastStore';

interface SurveyBuilderProps {
  onBack: () => void;
  onSave: () => void;
}

const questionTypes = [
  {
    id: 'single-choice' as const,
    label: 'Jednokrotny wybór',
    icon: RadioButton,
    description: 'Przyciski opcji - tylko jedna odpowiedź'
  },
  {
    id: 'multiple-choice' as const,
    label: 'Wielokrotny wybór',
    icon: CheckSquare,
    description: 'Pola wyboru - wiele odpowiedzi dozwolone'
  },
  {
    id: 'rating-scale' as const,
    label: 'Skala ocen',
    icon: BarChart3,
    description: 'Skala 1-5 lub 1-10 punktów'
  },
  {
    id: 'open-text' as const,
    label: 'Tekst otwarty',
    icon: FileText,
    description: 'Odpowiedź tekstowa'
  }
];

export function SurveyBuilder({ onBack, onSave }: SurveyBuilderProps) {
  const { selectedProject } = useAppStore();
  const queryClient = useQueryClient();

  const [surveyTitle, setSurveyTitle] = useState('');
  const [surveyDescription, setSurveyDescription] = useState('');
  const [targetResponses, setTargetResponses] = useState('1000');
  const [questions, setQuestions] = useState<Question[]>([]);

  const createMutation = useMutation({
    mutationFn: () => {
      const payload = {
        title: surveyTitle,
        description: surveyDescription || undefined,
        questions,
        target_responses: parseInt(targetResponses),
      };
      return surveysApi.create(selectedProject!.id, payload);
    },
    onSuccess: (createdSurvey) => {
      queryClient.invalidateQueries({ queryKey: ['surveys', selectedProject?.id] });
      toast.success('Ankieta utworzona', `${createdSurvey.title} · ${selectedProject?.name || 'Nieznany projekt'}`);
      onSave();
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Nieznany błąd';
      toast.error('Nie udało się utworzyć ankiety', `${surveyTitle || 'Nowa ankieta'} · ${selectedProject?.name || 'Nieznany projekt'} • ${message}`);
    },
  });

  const addQuestion = (type: Question['type']) => {
    const newQuestion: Question = {
      id: `question-${Date.now()}`,
      type,
      title: '',
      required: true,
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

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    if (result.source.droppableId === 'question-types' && result.destination.droppableId === 'survey-questions') {
      const questionType = questionTypes[result.source.index];
      addQuestion(questionType.id);
    } else if (result.source.droppableId === 'survey-questions' && result.destination.droppableId === 'survey-questions') {
      const items = Array.from(questions);
      const [reorderedItem] = items.splice(result.source.index, 1);
      items.splice(result.destination.index, 0, reorderedItem);
      setQuestions(items);
    }
  };

  const handleSave = () => {
    createMutation.mutate();
  };

  const isValid = surveyTitle && selectedProject && questions.length > 0 &&
    questions.every(q => q.title.trim() !== '');

  const getQuestionIcon = (type: string) => {
    const questionType = questionTypes.find(qt => qt.id === type);
    return questionType?.icon || FileText;
  };

  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Najpierw wybierz projekt</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="max-w-7xl mx-auto space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Wróć
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-foreground">Kreator ankiet</h1>
            <p className="text-muted-foreground">Utwórz nową syntetyczną ankietę</p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              disabled={!isValid || createMutation.isPending}
              className="bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              <Plus className="w-4 h-4 mr-2" />
              {createMutation.isPending ? 'Tworzenie...' : 'Utwórz ankietę'}
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
                  Typy pytań
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Droppable droppableId="question-types" isDropDisabled={true}>
                  {(provided) => (
                    <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-2">
                      {questionTypes.map((type, index) => (
                        <Draggable key={type.id} draggableId={type.id} index={index}>
                          {(provided, snapshot) => (
                            <>
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className={`p-3 rounded-lg border border-border bg-muted/30 cursor-grab active:cursor-grabbing hover:bg-muted/50 transition-colors ${
                                  snapshot.isDragging ? 'opacity-50' : ''
                                }`}
                              >
                                <div className="flex items-start gap-3">
                                  <type.icon className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm text-card-foreground font-medium">{type.label}</p>
                                    <p className="text-xs text-muted-foreground">{type.description}</p>
                                  </div>
                                </div>
                              </div>
                              {snapshot.isDragging && (
                                <div className="p-3 rounded-lg border-2 border-dashed border-primary/50 bg-primary/5">
                                  <div className="flex items-start gap-3">
                                    <type.icon className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm text-card-foreground font-medium">{type.label}</p>
                                      <p className="text-xs text-muted-foreground">{type.description}</p>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
                <Separator className="my-4" />
                <div className="space-y-2 text-xs text-muted-foreground">
                  <p>💡 Przeciągnij typy pytań do obszaru ankiety</p>
                  <p>🔄 Zmień kolejność pytań przeciągając</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Survey Builder */}
          <div className="lg:col-span-3 space-y-6">
            {/* Survey Configuration */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-card-foreground">Konfiguracja ankiety</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Tytuł ankiety *</Label>
                  <Input
                    id="title"
                    value={surveyTitle}
                    onChange={(e) => setSurveyTitle(e.target.value)}
                    placeholder="np. Preferencje funkcji produktu"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Opis</Label>
                  <Textarea
                    id="description"
                    value={surveyDescription}
                    onChange={(e) => setSurveyDescription(e.target.value)}
                    placeholder="Krótki opis tego, co ankieta ma odkryć"
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="targetResponses">Docelowa liczba odpowiedzi</Label>
                  <Select value={targetResponses} onValueChange={setTargetResponses}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="500">500</SelectItem>
                      <SelectItem value="1000">1,000</SelectItem>
                      <SelectItem value="2500">2,500</SelectItem>
                      <SelectItem value="5000">5,000</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Liczba odpowiedzi wygenerowanych przez AI na podstawie person projektu
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Survey Questions */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-card-foreground flex items-center justify-between">
                  Pytania ankiety
                  <Badge variant="outline">
                    {questions.length} {questions.length === 1 ? 'pytanie' : questions.length < 5 ? 'pytania' : 'pytań'}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Droppable droppableId="survey-questions">
                  {(provided, snapshot) => (
                    <div
                      {...provided.droppableProps}
                      ref={provided.innerRef}
                      className={`space-y-4 min-h-[200px] rounded-lg transition-colors ${
                        snapshot.isDraggingOver ? 'bg-primary/5 border-2 border-dashed border-primary' : 'border-2 border-dashed border-transparent'
                      } p-4`}
                    >
                      {questions.length === 0 ? (
                        <div className="text-center py-12">
                          <p className="text-muted-foreground">Przeciągnij typy pytań tutaj, aby rozpocząć tworzenie ankiety</p>
                        </div>
                      ) : (
                        questions.map((question, index) => {
                          const QuestionIcon = getQuestionIcon(question.type);
                          return (
                            <Draggable key={question.id} draggableId={question.id} index={index}>
                              {(provided) => (
                                <div
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  className="bg-muted/30 border border-border rounded-lg p-4"
                                >
                                  <div className="flex items-start gap-3">
                                    <div {...provided.dragHandleProps} className="cursor-grab active:cursor-grabbing pt-1">
                                      <GripVertical className="w-5 h-5 text-muted-foreground" />
                                    </div>
                                    <QuestionIcon className="w-5 h-5 text-primary flex-shrink-0 mt-1" />
                                    <div className="flex-1 space-y-3">
                                      <div className="flex items-start justify-between gap-2">
                                        <Input
                                          value={question.title}
                                          onChange={(e) => updateQuestion(question.id, { title: e.target.value })}
                                          placeholder="Wpisz swoje pytanie"
                                          className="flex-1"
                                        />
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => deleteQuestion(question.id)}
                                          className="text-red-600 hover:text-red-700"
                                        >
                                          <Trash2 className="w-4 h-4" />
                                        </Button>
                                      </div>

                                      {/* Question Type Specific Fields */}
                                      {(question.type === 'single-choice' || question.type === 'multiple-choice') && question.options && (
                                        <div className="space-y-2 pl-2">
                                          {question.options.map((option, optionIndex) => (
                                            <div key={optionIndex} className="flex items-center gap-2">
                                              {question.type === 'single-choice' ? (
                                                <div className="w-4 h-4 rounded-full border-2 border-muted-foreground flex-shrink-0" />
                                              ) : (
                                                <div className="w-4 h-4 rounded border-2 border-muted-foreground flex-shrink-0" />
                                              )}
                                              <Input
                                                value={option}
                                                onChange={(e) => updateOption(question.id, optionIndex, e.target.value)}
                                                placeholder={`Opcja ${optionIndex + 1}`}
                                                className="flex-1 h-8"
                                              />
                                              {question.options && question.options.length > 2 && (
                                                <Button
                                                  variant="ghost"
                                                  size="sm"
                                                  onClick={() => removeOption(question.id, optionIndex)}
                                                  className="h-8 w-8 p-0"
                                                >
                                                  <Trash2 className="w-3 h-3" />
                                                </Button>
                                              )}
                                            </div>
                                          ))}
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => addOption(question.id)}
                                            className="ml-6"
                                          >
                                            <Plus className="w-3 h-3 mr-1" />
                                            Dodaj opcję
                                          </Button>
                                        </div>
                                      )}

                                      {question.type === 'rating-scale' && (
                                        <div className="flex items-center gap-4 pl-2">
                                          <div className="flex items-center gap-2">
                                            <Label className="text-xs">Min:</Label>
                                            <Input
                                              type="number"
                                              value={question.scaleMin}
                                              onChange={(e) => updateQuestion(question.id, { scaleMin: parseInt(e.target.value) || 1 })}
                                              className="w-16 h-8"
                                            />
                                          </div>
                                          <div className="flex items-center gap-2">
                                            <Label className="text-xs">Maks:</Label>
                                            <Input
                                              type="number"
                                              value={question.scaleMax}
                                              onChange={(e) => updateQuestion(question.id, { scaleMax: parseInt(e.target.value) || 5 })}
                                              className="w-16 h-8"
                                            />
                                          </div>
                                        </div>
                                      )}

                                      <div className="flex items-center gap-2">
                                        <Switch
                                          checked={question.required}
                                          onCheckedChange={(checked) => updateQuestion(question.id, { required: checked })}
                                        />
                                        <Label className="text-sm text-muted-foreground">Pytanie wymagane</Label>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </Draggable>
                          );
                        })
                      )}
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
    </div>
  );
}
