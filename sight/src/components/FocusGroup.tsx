import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Checkbox } from './ui/checkbox';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { ArrowLeft, Settings as SettingsIcon, MessageSquare, BarChart3, Play, Loader2, Clock, CheckCircle, Plus, Trash2 } from 'lucide-react';
import { ScoreChart } from './ScoreChart';

interface FocusGroupProps {
  focusGroup: any;
  onBack: () => void;
}

const mockPersonas = [
  { id: 1, name: "Sarah Johnson", age: 28, occupation: "Marketing Manager" },
  { id: 2, name: "Michael Chen", age: 34, occupation: "Software Engineer" },
  { id: 3, name: "Emily Rodriguez", age: 42, occupation: "Small Business Owner" },
  { id: 4, name: "David Kim", age: 29, occupation: "Designer" },
  { id: 5, name: "Lisa Thompson", age: 36, occupation: "Teacher" }
];

const sentimentData = [
  { name: 'Very Positive', value: 35, color: '#10B981' },
  { name: 'Positive', value: 28, color: '#34D399' },
  { name: 'Neutral', value: 22, color: '#6B7280' },
  { name: 'Negative', value: 12, color: '#F59E0B' },
  { name: 'Very Negative', value: 3, color: '#EF4444' }
];

const keywordsData = [
  { word: 'Easy', count: 24 },
  { word: 'Useful', count: 19 },
  { word: 'Expensive', count: 15 },
  { word: 'Innovative', count: 13 },
  { word: 'Confusing', count: 8 }
];

const mockResponses = [
  {
    question: "What features are most important to you?",
    responses: [
      { persona: "Sarah Johnson", response: "I value ease of use and integration with existing tools. Time-saving features are crucial for my workflow." },
      { persona: "Michael Chen", response: "Advanced customization options and API access are important. I need flexibility for different use cases." },
      { persona: "Emily Rodriguez", response: "Cost-effectiveness and reliability are my top priorities. I need something that works consistently." }
    ]
  },
  {
    question: "How would you use this product?",
    responses: [
      { persona: "Sarah Johnson", response: "Primarily for campaign management and team collaboration. Would use it daily for project planning." },
      { persona: "Michael Chen", response: "For prototyping and development workflows. Integration with development tools would be essential." },
      { persona: "Emily Rodriguez", response: "To streamline business operations and improve customer communication. Need mobile access." }
    ]
  }
];

export function FocusGroup({ focusGroup, onBack }: FocusGroupProps) {
  const [selectedParticipants, setSelectedParticipants] = useState<number[]>(
    focusGroup?.participants && Array.isArray(focusGroup.participants) ? focusGroup.participants : []
  );
  const [isRunning, setIsRunning] = useState(false);
  const [discussionProgress, setDiscussionProgress] = useState(0);
  const [discussionComplete, setDiscussionComplete] = useState(focusGroup.status === 'Completed');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [questions, setQuestions] = useState<string[]>(focusGroup?.questions || []);
  const [newQuestion, setNewQuestion] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{id: number, persona: string, message: string, timestamp: string}>>([]);
  const [activeTab, setActiveTab] = useState('setup');

  const handleParticipantToggle = (personaId: number) => {
    setSelectedParticipants(prev => {
      const currentParticipants = Array.isArray(prev) ? prev : [];
      return currentParticipants.includes(personaId) 
        ? currentParticipants.filter(id => id !== personaId)
        : [...currentParticipants, personaId];
    });
  };

  const handleRunDiscussion = () => {
    setIsRunning(true);
    setDiscussionProgress(0);
    setChatMessages([]);
    
    const interval = setInterval(() => {
      setDiscussionProgress(prev => {
        // Add chat messages during progress
        if (prev === 15) {
          setChatMessages([
            {id: 1, persona: "Sarah Johnson", message: "I really appreciate tools that integrate well with my existing workflow. Time-saving is key for me.", timestamp: "14:32"}
          ]);
        }
        if (prev === 35) {
          setChatMessages(prev => [...prev, 
            {id: 2, persona: "Michael Chen", message: "For me, the technical aspects matter most. I need flexibility and customization options.", timestamp: "14:33"}
          ]);
        }
        if (prev === 55) {
          setChatMessages(prev => [...prev, 
            {id: 3, persona: "Emily Rodriguez", message: "Cost is definitely a factor for small businesses like mine. But reliability is even more important.", timestamp: "14:34"}
          ]);
        }
        if (prev === 75) {
          setChatMessages(prev => [...prev, 
            {id: 4, persona: "David Kim", message: "The user interface needs to be intuitive. I don't want to spend hours learning a new tool.", timestamp: "14:35"}
          ]);
        }
        
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          setDiscussionComplete(true);
          return 100;
        }
        return prev + 5;
      });
    }, 500);
  };

  const addQuestion = () => {
    if (newQuestion.trim()) {
      setQuestions([...questions, newQuestion.trim()]);
      setNewQuestion('');
    }
  };

  const removeQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  // Handle case where focusGroup is null or undefined
  if (!focusGroup) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            onClick={onBack}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Focus Groups
          </Button>
          <div>
            <h1 className="text-3xl font-semibold text-foreground">Focus Group Not Found</h1>
            <p className="text-muted-foreground">The requested focus group could not be loaded.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="ghost" 
          onClick={onBack}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Focus Groups
        </Button>
        <div>
          <h1 className="text-3xl font-semibold text-foreground">{focusGroup.name || focusGroup.title || 'Unnamed Focus Group'}</h1>
          <div className="flex items-center gap-3 mt-1">
            <Badge className={
              focusGroup.status === 'Active' || focusGroup.status === 'running'
                ? 'bg-chart-2/20 text-chart-2 border-chart-2/30' 
                : focusGroup.status === 'Completed' || focusGroup.status === 'completed'
                ? 'bg-chart-1/20 text-chart-1 border-chart-1/30'
                : 'bg-muted text-muted-foreground border-border'
            }>
              {focusGroup.status === 'completed' ? 'Completed' : (focusGroup.status || 'Planning')}
            </Badge>
            <span className="text-muted-foreground">•</span>
            <span className="text-muted-foreground">{focusGroup.questions?.length || focusGroup.discussionTopics?.length || 0} questions</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-muted border border-border shadow-sm">
          <TabsTrigger value="setup" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <SettingsIcon className="w-4 h-4 mr-2" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="discussion" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <MessageSquare className="w-4 h-4 mr-2" />
            Discussion
          </TabsTrigger>
          <TabsTrigger value="results" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            Results & Analysis
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="setup" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Questions */}
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-card-foreground">Discussion Questions</CardTitle>
                <p className="text-muted-foreground">Questions that will be asked during the focus group session</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {questions.map((question: string, index: number) => (
                    <div key={index} className="p-3 bg-muted rounded-lg border border-border">
                      <div className="flex items-start gap-3">
                        <span className="text-sm font-medium text-brand-orange bg-brand-orange/10 px-2 py-1 rounded">
                          Q{index + 1}
                        </span>
                        <p className="text-foreground flex-1">{question}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeQuestion(index)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {questions.length === 0 && (
                    <p className="text-muted-foreground text-center py-4">No questions configured</p>
                  )}
                </div>
                
                <div className="mt-4 pt-4 border-t border-border">
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <Label htmlFor="new-question" className="sr-only">Add Question</Label>
                      <Input
                        id="new-question"
                        placeholder="Enter a new discussion question..."
                        value={newQuestion}
                        onChange={(e) => setNewQuestion(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && addQuestion()}
                      />
                    </div>
                    <Button
                      onClick={addQuestion}
                      disabled={!newQuestion.trim()}
                      className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Participants */}
            <Card className="bg-card border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-card-foreground">Select Participants</CardTitle>
                <p className="text-muted-foreground">Choose personas to participate in this focus group</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockPersonas.map((persona) => (
                    <div key={persona.id} className="flex items-center space-x-3 p-3 bg-muted rounded-lg border border-border">
                      <Checkbox
                        id={`persona-${persona.id}`}
                        checked={Array.isArray(selectedParticipants) && selectedParticipants.includes(persona.id)}
                        onCheckedChange={() => handleParticipantToggle(persona.id)}
                      />
                      <div className="flex-1">
                        <label 
                          htmlFor={`persona-${persona.id}`}
                          className="text-card-foreground font-medium cursor-pointer"
                        >
                          {persona.name}
                        </label>
                        <p className="text-sm text-muted-foreground">{persona.age} years old • {persona.occupation}</p>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-sm text-muted-foreground">
                    {selectedParticipants.length} participants selected
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Discussion Tab */}
        <TabsContent value="discussion" className="space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-card-foreground">Run Discussion</CardTitle>
                  <p className="text-muted-foreground">Start the AI-simulated focus group discussion</p>
                </div>
                
                {!discussionComplete && !isRunning && (
                  <Button 
                    onClick={handleRunDiscussion}
                    className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                    disabled={!Array.isArray(selectedParticipants) || selectedParticipants.length === 0}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Discussion
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {!isRunning && !discussionComplete && (
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-card-foreground mb-2">Ready to Start</h3>
                  <p className="text-muted-foreground">
                    {Array.isArray(selectedParticipants) && selectedParticipants.length > 0 
                      ? `${selectedParticipants.length} participants selected. Click "Start Discussion" to begin the simulation.`
                      : 'Please select participants in the Configuration tab first.'
                    }
                  </p>
                </div>
              )}

              {isRunning && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    <span className="text-card-foreground">Simulation in progress...</span>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Discussion Progress</span>
                      <span className="text-muted-foreground">{discussionProgress}%</span>
                    </div>
                    <Progress value={discussionProgress} className="w-full" />
                  </div>
                  
                  <div className="bg-muted rounded-lg p-4 border border-border">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-primary" />
                        <span className="text-muted-foreground">Current Status:</span>
                      </div>
                      <p className="text-card-foreground">
                        {discussionProgress < 30 && "Participants are introducing themselves..."}
                        {discussionProgress >= 30 && discussionProgress < 60 && "Discussing question 1 of " + questions.length}
                        {discussionProgress >= 60 && discussionProgress < 90 && "Exploring follow-up questions..."}
                        {discussionProgress >= 90 && "Wrapping up discussion..."}
                      </p>
                    </div>
                  </div>
                  
                  {chatMessages.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-4">
                      <h4 className="text-card-foreground font-medium mb-3">Live Discussion</h4>
                      <div className="space-y-3 max-h-48 overflow-y-auto">
                        {chatMessages.map((message) => (
                          <div key={message.id} className="flex gap-3 animate-in slide-in-from-bottom-2 duration-300">
                            <div className="w-8 h-8 bg-brand-orange rounded-full flex items-center justify-center shrink-0">
                              <span className="text-white text-xs font-medium">
                                {message.persona.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-card-foreground font-medium text-sm">{message.persona}</span>
                                <span className="text-muted-foreground text-xs">{message.timestamp}</span>
                              </div>
                              <div className="bg-muted/50 rounded-lg p-3 border border-border/50">
                                <p className="text-card-foreground text-sm">{message.message}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {discussionComplete && (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-brand-orange mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-brand-orange mb-2">Discussion Complete</h3>
                  <p className="text-muted-foreground mb-4">
                    The focus group simulation has finished. View the results in the "Results & Analysis" tab.
                  </p>
                  <Button 
                    variant="outline"
                    onClick={() => setActiveTab('results')}
                    className="border-border text-card-foreground hover:text-card-foreground"
                  >
                    View Results
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {discussionComplete ? (
            <>
              {/* AI Summary */}
              <Card className="bg-card border border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-card-foreground">AI Summary</CardTitle>
                  <p className="text-muted-foreground">Key insights generated by AI analysis</p>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-muted p-4 rounded-lg border border-border">
                      <h4 className="text-card-foreground font-medium mb-2">Executive Summary</h4>
                      <p className="text-muted-foreground text-sm">
                        Participants showed strong interest in ease-of-use features and integration capabilities. 
                        Pricing concerns were raised by 60% of participants, suggesting value proposition optimization.
                      </p>
                    </div>
                    
                    <div className="bg-muted p-4 rounded-lg border border-border">
                      <h4 className="text-card-foreground font-medium mb-2">Key Insights</h4>
                      <ul className="text-muted-foreground text-sm space-y-1">
                        <li>• Usability is the primary concern</li>
                        <li>• Mobile access is highly valued</li>
                        <li>• Integration needs vary by role</li>
                        <li>• Price sensitivity across segments</li>
                      </ul>
                    </div>
                    
                    <div className="bg-muted p-4 rounded-lg border border-border">
                      <h4 className="text-card-foreground font-medium mb-2">Recommendations</h4>
                      <ul className="text-muted-foreground text-sm space-y-1">
                        <li>• Prioritize UX improvements</li>
                        <li>• Develop mobile-first approach</li>
                        <li>• Create tiered pricing model</li>
                        <li>• Focus on integration features</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Statistics */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-card border border-border shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-card-foreground">Sentiment Analysis</CardTitle>
                    <p className="text-muted-foreground">Overall sentiment distribution</p>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-col items-center space-y-6">
                      {/* Legend */}
                      <div className="flex gap-6 items-center">
                        {sentimentData.map((entry, index) => (
                          <div key={index} className="flex items-center gap-2">
                            <div 
                              className="w-6 h-3 rounded-full" 
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-sm text-card-foreground">{entry.name}</span>
                          </div>
                        ))}
                      </div>
                      
                      {/* Doughnut Chart */}
                      <div className="relative w-64 h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={sentimentData}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={100}
                              dataKey="value"
                              startAngle={0}
                              endAngle={360}
                            >
                              {sentimentData.map((entry, index) => (
                                <Cell 
                                  key={`cell-${index}`} 
                                  fill={entry.color}
                                  stroke={hoveredIndex === index ? "#333333" : entry.color}
                                  strokeWidth={hoveredIndex === index ? 3 : 0}
                                  style={{ 
                                    cursor: 'pointer',
                                    filter: hoveredIndex === index ? 'drop-shadow(0px 4px 8px rgba(0,0,0,0.15))' : 'none',
                                    transition: 'all 0.2s ease'
                                  }}
                                  onMouseEnter={() => setHoveredIndex(index)}
                                  onMouseLeave={() => setHoveredIndex(null)}
                                />
                              ))}
                            </Pie>
                            <Tooltip 
                              content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                  const data = payload[0].payload;
                                  return (
                                    <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
                                      <p className="text-popover-foreground font-medium">{data.name}</p>
                                      <p className="text-popover-foreground text-sm">{data.value}%</p>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                        {/* Center percentage */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          {/* Center area - now empty for cleaner look */}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-card border border-border shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-card-foreground">Score Analysis</CardTitle>
                    <p className="text-muted-foreground">Overall participant satisfaction score</p>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64 flex items-start justify-center pt-4">
                      <ScoreChart />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Raw Responses */}
              <Card className="bg-card border border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-card-foreground">Raw Responses</CardTitle>
                  <p className="text-muted-foreground">Detailed responses from each participant</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {mockResponses.map((item, index) => (
                      <div key={index} className="space-y-3">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-brand-orange bg-brand-orange/10 px-3 py-1 rounded">
                            Q{index + 1}
                          </span>
                          <h4 className="text-card-foreground font-medium">{item.question}</h4>
                        </div>
                        
                        <div className="space-y-3 ml-12">
                          {item.responses.map((response, respIndex) => (
                            <div key={respIndex} className="bg-muted p-4 rounded-lg border border-border">
                              <div className="flex items-center gap-2 mb-2">
                                <div className="w-8 h-8 bg-brand-orange rounded-full flex items-center justify-center">
                                  <span className="text-white text-xs font-medium">
                                    {response.persona.split(' ').map(n => n[0]).join('')}
                                  </span>
                                </div>
                                <span className="text-card-foreground font-medium">{response.persona}</span>
                              </div>
                              <p className="text-muted-foreground text-sm">{response.response}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="bg-card border border-border shadow-sm">
              <CardContent className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-card-foreground mb-2">No Results Yet</h3>
                <p className="text-muted-foreground">
                  Run the discussion simulation first to generate analysis and insights.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}