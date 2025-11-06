import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { ScrollArea } from '../ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/separator';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import { 
  User, 
  Brain,
  Sparkles,
  Target,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  TrendingUp,
  Quote
} from 'lucide-react';

interface Persona {
  id: number;
  name: string;
  age: number;
  occupation: string;
  interests: string[];
  background: string;
  demographics: {
    gender: string;
    location: string;
    income: string;
    education: string;
  };
  psychographics: {
    personality: string[];
    values: string[];
    lifestyle: string;
  };
  behaviorProfiles?: {
    techSavviness: number;
    brandLoyalty: number;
    priceSensitivity: number;
    riskTolerance: number;
  };
  createdAt: string;
  projectId: number;
}

interface PersonaDetailsDrawerProps {
  persona: Persona | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Mock data generators
const generateSegmentData = (persona: Persona) => {
  const segmentName = persona.id === 1 || persona.id === 4 
    ? 'Tech-Savvy Professionals' 
    : persona.id === 3 
    ? 'Practical Entrepreneurs' 
    : 'Creative Innovators';

  return {
    name: segmentName,
    size: '35%',
    characteristics: [
      'Data-driven decision making',
      'Early tech adopters',
      'Efficiency-focused'
    ]
  };
};

const generateJTBD = (persona: Persona) => {
  return [
    {
      statement: `When managing projects, I need to automate repetitive tasks so I can focus on strategic work`,
      priority: 9,
      frequency: 'Daily',
      quotes: ['I spend 3 hours daily copying data between systems']
    },
    {
      statement: `When planning budget, I need to quickly assess ROI from different investments`,
      priority: 8,
      frequency: 'Monthly',
      quotes: ['CFO requires specific numbers that I don\'t have in one place']
    }
  ];
};

const generateDesiredOutcomes = () => {
  return [
    {
      statement: 'Reduce time spent on reporting by 50%',
      opportunityScore: 85,
      importance: 9,
      satisfaction: 4
    },
    {
      statement: 'Increase project visibility in real-time',
      opportunityScore: 78,
      importance: 8,
      satisfaction: 5
    }
  ];
};

const generatePainPoints = (persona: Persona) => {
  return [
    {
      title: 'Too many tools - no integration',
      description: `As a ${persona.occupation}, I use 5+ different applications daily. Data is scattered, and context switching takes time and energy.`,
      severity: 'High' as const,
      frequency: 'Daily',
      quotes: ['I have to log into 6 different systems every day']
    },
    {
      title: 'No time for strategic thinking',
      description: '80% of time goes to operational tasks. No space for deep work and long-term planning.',
      severity: 'Critical' as const,
      frequency: 'Constantly',
      quotes: []
    }
  ];
};

export function PersonaDetailsDrawer({ 
  persona, 
  open, 
  onOpenChange
}: PersonaDetailsDrawerProps) {
  if (!persona) return null;

  const segmentData = generateSegmentData(persona);
  const jtbdData = generateJTBD(persona);
  const outcomesData = generateDesiredOutcomes();
  const painPointsData = generatePainPoints(persona);

  const getPriorityColor = (priority: number) => {
    if (priority >= 8) return 'bg-brand-orange text-white';
    if (priority >= 6) return 'bg-brand-gold text-white';
    return 'bg-muted text-muted-foreground';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Critical': return 'bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400 border-red-300 dark:border-red-800';
      case 'High': return 'bg-orange-100 dark:bg-orange-950/30 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-800';
      case 'Medium': return 'bg-yellow-100 dark:bg-yellow-950/30 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-800';
      default: return 'bg-blue-100 dark:bg-blue-950/30 text-blue-700 dark:text-blue-400 border-blue-300 dark:border-blue-800';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} modal>
      <DialogContent 
        className="max-w-[95vw] w-full lg:max-w-[1000px] h-[90vh] p-0 gap-0 overflow-hidden flex flex-col bg-background"
      >
        <DialogHeader className="sr-only">
          <DialogTitle>{persona.name}</DialogTitle>
          <DialogDescription>Detailed persona profile</DialogDescription>
        </DialogHeader>

        {/* Compact Header */}
        <div className="px-8 py-6 border-b border-border bg-muted/20">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h2 className="mb-2">{persona.name}</h2>
              <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span>{persona.age} years old</span>
                <span>•</span>
                <span>{persona.occupation}</span>
                <span>•</span>
                <span>{persona.demographics.location}</span>
              </div>
            </div>
            <Badge className="bg-brand-orange text-white shrink-0">
              AI Generated
            </Badge>
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="p-8 space-y-8">
            
            {/* Quick Stats Bar */}
            {persona.behaviorProfiles && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="border-border bg-card/50">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl mb-1 text-brand-orange">
                      {persona.behaviorProfiles.techSavviness}/10
                    </div>
                    <p className="text-xs text-muted-foreground">Tech Savviness</p>
                  </CardContent>
                </Card>
                <Card className="border-border bg-card/50">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl mb-1 text-brand-orange">
                      {persona.behaviorProfiles.brandLoyalty}/10
                    </div>
                    <p className="text-xs text-muted-foreground">Brand Loyalty</p>
                  </CardContent>
                </Card>
                <Card className="border-border bg-card/50">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl mb-1 text-brand-orange">
                      {persona.behaviorProfiles.priceSensitivity}/10
                    </div>
                    <p className="text-xs text-muted-foreground">Price Sensitivity</p>
                  </CardContent>
                </Card>
                <Card className="border-border bg-card/50">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl mb-1 text-brand-orange">
                      {persona.behaviorProfiles.riskTolerance}/10
                    </div>
                    <p className="text-xs text-muted-foreground">Risk Tolerance</p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Background */}
            <section>
              <h3 className="mb-4">Background</h3>
              <Card className="border-border">
                <CardContent className="pt-6">
                  <p className="text-foreground leading-relaxed">
                    {persona.background}
                  </p>
                </CardContent>
              </Card>
            </section>

            {/* Profile Grid */}
            <section>
              <h3 className="mb-4">Profile</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Demographics */}
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <User className="w-4 h-4 text-brand-orange" />
                      Demographics
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <dl className="space-y-3">
                      <div className="flex justify-between">
                        <dt className="text-sm text-muted-foreground">Gender</dt>
                        <dd className="text-sm text-foreground">{persona.demographics.gender}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-muted-foreground">Age</dt>
                        <dd className="text-sm text-foreground">{persona.age} years</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-muted-foreground">Education</dt>
                        <dd className="text-sm text-foreground">{persona.demographics.education}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-muted-foreground">Income</dt>
                        <dd className="text-sm text-foreground">{persona.demographics.income}</dd>
                      </div>
                    </dl>
                  </CardContent>
                </Card>

                {/* Psychographics */}
                <Card className="border-border">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Brain className="w-4 h-4 text-brand-orange" />
                      Psychographics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Personality</p>
                      <div className="flex flex-wrap gap-2">
                        {persona.psychographics.personality.map((trait, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{trait}</Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Values</p>
                      <div className="flex flex-wrap gap-2">
                        {persona.psychographics.values.map((value, i) => (
                          <Badge 
                            key={i} 
                            className="bg-brand-orange/10 text-brand-orange border-brand-orange/30 text-xs"
                          >
                            {value}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Interests</p>
                      <div className="flex flex-wrap gap-2">
                        {persona.interests.map((interest, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{interest}</Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </section>

            {/* Segment */}
            <section>
              <h3 className="mb-4">Segment</h3>
              <Card className="border-brand-orange/30 bg-gradient-to-br from-brand-orange/5 to-brand-gold/5">
                <CardHeader>
                  <div className="flex items-center justify-between gap-4">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-brand-orange" />
                      {segmentData.name}
                    </CardTitle>
                    <Badge variant="outline" className="shrink-0">
                      {segmentData.size} of market
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {segmentData.characteristics.map((char, idx) => (
                      <Badge 
                        key={idx} 
                        variant="secondary" 
                        className="bg-background/50 border border-border text-xs"
                      >
                        {char}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </section>

            <Separator />

            {/* Jobs To Be Done */}
            <section>
              <h3 className="mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-brand-orange" />
                Jobs To Be Done
              </h3>
              <div className="space-y-4">
                {jtbdData.map((job, idx) => (
                  <Card key={idx} className="border-border">
                    <CardContent className="pt-6 space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <p className="text-foreground flex-1">{job.statement}</p>
                        <Badge className={getPriorityColor(job.priority)} className="shrink-0">
                          {job.priority}/10
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-muted-foreground">
                          Frequency: <span className="text-foreground">{job.frequency}</span>
                        </span>
                      </div>
                      
                      {job.quotes.length > 0 && (
                        <div className="pt-3 border-t border-border">
                          {job.quotes.map((quote, qIdx) => (
                            <div key={qIdx} className="flex gap-2 items-start">
                              <Quote className="w-4 h-4 text-brand-gold shrink-0 mt-0.5" />
                              <p className="text-sm text-muted-foreground italic">"{quote}"</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* Desired Outcomes */}
            <section>
              <h3 className="mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                Desired Outcomes
              </h3>
              <div className="space-y-4">
                {outcomesData.map((outcome, idx) => (
                  <Card key={idx} className="border-border">
                    <CardContent className="pt-6 space-y-3">
                      <p className="text-foreground">{outcome.statement}</p>
                      
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground">Opportunity</span>
                        <Progress value={outcome.opportunityScore} className="flex-1 h-2" />
                        <span className="text-sm text-brand-orange">{outcome.opportunityScore}/100</span>
                      </div>
                      
                      <div className="flex gap-6 text-sm pt-2 border-t border-border">
                        <div>
                          <span className="text-muted-foreground">Importance: </span>
                          <span className="text-foreground">{outcome.importance}/10</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Satisfaction: </span>
                          <span className="text-foreground">{outcome.satisfaction}/10</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* Pain Points */}
            <section>
              <h3 className="mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Pain Points
              </h3>
              <div className="space-y-4">
                {painPointsData.map((pain, idx) => (
                  <Card key={idx} className="border-border">
                    <CardContent className="pt-6 space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <h4 className="flex-1">{pain.title}</h4>
                        <Badge variant="outline" className={getSeverityColor(pain.severity)}>
                          {pain.severity}
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-muted-foreground">{pain.description}</p>
                      
                      <div className="text-sm">
                        <span className="text-muted-foreground">Frequency: </span>
                        <span className="text-foreground">{pain.frequency}</span>
                      </div>

                      {pain.quotes.length > 0 && (
                        <div className="pt-3 border-t border-border">
                          {pain.quotes.map((quote, qIdx) => (
                            <div key={qIdx} className="flex gap-2 items-start">
                              <Quote className="w-4 h-4 text-brand-gold shrink-0 mt-0.5" />
                              <p className="text-sm text-muted-foreground italic">"{quote}"</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* Footer */}
            <div className="pt-4 text-center">
              <p className="text-sm text-muted-foreground">
                Generated on {new Date(persona.createdAt).toLocaleDateString('en-US', { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </p>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
