import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';
import { Textarea } from './ui/textarea';
import { Plus, Users, Brain, ArrowRight, ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react';
import { PersonaGenerationWizard } from './PersonaGenerationWizard';
import { PersonaDetailsDrawer } from './personas/PersonaDetailsDrawer';
import { toast } from 'sonner@2.0.3';
import Slider from 'react-slick';

interface PersonasProps {}

interface Project {
  id: number;
  name: string;
  description: string;
}

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



const mockProjects: Project[] = [
  {
    id: 1,
    name: "Mobile App Launch Research",
    description: "Research for new mobile application targeting millennials"
  },
  {
    id: 2,
    name: "Product Development Study",
    description: "Understanding user needs for next product iteration"
  },
  {
    id: 3,
    name: "Marketing Research",
    description: "Brand perception and market positioning analysis"
  }
];

const mockPersonas: Persona[] = [
  {
    id: 1,
    name: "Sarah Johnson",
    age: 28,
    occupation: "Marketing Manager",
    interests: ["Technology", "Travel", "Fitness", "Sustainability"],
    background: "Tech-savvy professional who values work-life balance and sustainable living. Early adopter of new technologies with strong influence in her professional network.",
    demographics: {
      gender: "Female",
      location: "San Francisco, CA",
      income: "$75,000 - $100,000",
      education: "Bachelor's Degree"
    },
    psychographics: {
      personality: ["Ambitious", "Creative", "Analytical"],
      values: ["Innovation", "Environment", "Work-life balance"],
      lifestyle: "Urban professional with active social life"
    },
    behaviorProfiles: {
      techSavviness: 9,
      brandLoyalty: 6,
      priceSensitivity: 5,
      riskTolerance: 7
    },
    createdAt: "2024-01-10",
    projectId: 1
  },
  {
    id: 2,
    name: "Michael Chen",
    age: 34,
    occupation: "Software Engineer",
    interests: ["Gaming", "Cooking", "Music", "Open Source"],
    background: "Early adopter and tech influencer who values quality and performance. Makes purchasing decisions based on detailed research and peer recommendations.",
    demographics: {
      gender: "Male",
      location: "Austin, TX",
      income: "$100,000 - $150,000",
      education: "Master's Degree"
    },
    psychographics: {
      personality: ["Logical", "Detail-oriented", "Collaborative"],
      values: ["Quality", "Innovation", "Community"],
      lifestyle: "Tech enthusiast with work-from-home flexibility"
    },
    behaviorProfiles: {
      techSavviness: 10,
      brandLoyalty: 4,
      priceSensitivity: 6,
      riskTolerance: 8
    },
    createdAt: "2024-01-12",
    projectId: 2
  },
  {
    id: 3,
    name: "Emily Rodriguez",
    age: 42,
    occupation: "Small Business Owner",
    interests: ["Family", "Community", "Business Development", "Networking"],
    background: "Practical decision-maker focused on value and reliability. Prioritizes solutions that help her business grow while maintaining family time.",
    demographics: {
      gender: "Female",
      location: "Denver, CO",
      income: "$50,000 - $75,000",
      education: "Associate Degree"
    },
    psychographics: {
      personality: ["Practical", "Caring", "Determined"],
      values: ["Family", "Reliability", "Growth"],
      lifestyle: "Busy entrepreneur balancing business and family"
    },
    behaviorProfiles: {
      techSavviness: 5,
      brandLoyalty: 8,
      priceSensitivity: 9,
      riskTolerance: 4
    },
    createdAt: "2024-01-15",
    projectId: 3
  },
  {
    id: 4,
    name: "David Kim",
    age: 26,
    occupation: "UX Designer",
    interests: ["Design", "Art", "Technology", "Mental Health"],
    background: "Creative professional passionate about user experience and accessibility. Values inclusive design and mental health awareness in the workplace.",
    demographics: {
      gender: "Male",
      location: "Seattle, WA",
      income: "$65,000 - $85,000",
      education: "Bachelor's Degree"
    },
    psychographics: {
      personality: ["Creative", "Empathetic", "Perfectionist"],
      values: ["Accessibility", "Creativity", "Wellness"],
      lifestyle: "Creative professional with strong social consciousness"
    },
    behaviorProfiles: {
      techSavviness: 8,
      brandLoyalty: 7,
      priceSensitivity: 6,
      riskTolerance: 6
    },
    createdAt: "2024-01-18",
    projectId: 1
  }
];



// Custom arrow components for carousel
const NextArrow = (props: any) => {
  const { onClick } = props;
  return (
    <button
      onClick={onClick}
      className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 bg-brand-orange hover:bg-brand-orange/90 text-white rounded-full shadow-lg flex items-center justify-center transition-all"
      style={{ transform: 'translate(50%, -50%)' }}
    >
      <ChevronRight className="w-5 h-5" />
    </button>
  );
};

const PrevArrow = (props: any) => {
  const { onClick } = props;
  return (
    <button
      onClick={onClick}
      className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-10 bg-brand-orange hover:bg-brand-orange/90 text-white rounded-full shadow-lg flex items-center justify-center transition-all"
      style={{ transform: 'translate(-50%, -50%)' }}
    >
      <ChevronLeft className="w-5 h-5" />
    </button>
  );
};

export function Personas({}: PersonasProps) {
  const [personas, setPersonas] = useState(mockPersonas);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [showPersonaWizard, setShowPersonaWizard] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>("1");
  const [showBehaviorSimulation, setShowBehaviorSimulation] = useState(false);
  const [simulationPersona, setSimulationPersona] = useState<Persona | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [customQuestion, setCustomQuestion] = useState('');
  
  // Filter personas by selected project
  const filteredPersonas = personas.filter(p => p.projectId === parseInt(selectedProject));

  // Calculate statistics
  const avgTechSavviness = filteredPersonas.reduce((sum, p) => sum + (p.behaviorProfiles?.techSavviness || 0), 0) / filteredPersonas.length;
  const avgBrandLoyalty = filteredPersonas.reduce((sum, p) => sum + (p.behaviorProfiles?.brandLoyalty || 0), 0) / filteredPersonas.length;
  const avgPriceSensitivity = filteredPersonas.reduce((sum, p) => sum + (p.behaviorProfiles?.priceSensitivity || 0), 0) / filteredPersonas.length;

  const handleGeneratePersonas = async (config: any) => {
    console.log('Generating personas with config:', config);
    toast.success('Personas generation started');
  };

  const handleOpenBehaviorSimulation = (persona: Persona) => {
    setSimulationPersona(persona);
    setSelectedScenario(null);
    setSimulationResult(null);
    setCustomQuestion('');
    setShowBehaviorSimulation(true);
  };

  const runCustomSimulation = async () => {
    if (!simulationPersona || !customQuestion.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setIsSimulating(true);
    setSelectedScenario('custom');

    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 1500));

    const profiles = simulationPersona.behaviorProfiles!;
    
    // Generate dynamic response based on behavior profiles
    const prediction = `Based on ${simulationPersona.name}'s profile, here's how they might respond`;
    const confidence = 70 + Math.floor(Math.random() * 20);
    
    const reasoning = [
      `Tech savviness (${profiles.techSavviness}/10) influences their comfort with new solutions`,
      `Brand loyalty (${profiles.brandLoyalty}/10) affects their openness to alternatives`,
      `Price sensitivity (${profiles.priceSensitivity}/10) impacts their budget considerations`,
      `Risk tolerance (${profiles.riskTolerance}/10) determines their willingness to try new approaches`
    ];

    const recommendation = `Given ${simulationPersona.name}'s profile, consider: ${
      profiles.techSavviness > 7 
        ? 'leading with technical benefits and innovation' 
        : 'emphasizing simplicity and proven results'
    }. ${
      profiles.priceSensitivity > 7
        ? 'Highlight ROI and cost savings clearly.'
        : 'Focus on premium value and quality.'
    }`;

    setSimulationResult({
      prediction,
      confidence,
      reasoning,
      recommendation,
      customQuestion: customQuestion
    });
    setIsSimulating(false);
  };



  const carouselSettings = {
    dots: true,
    infinite: filteredPersonas.length > 3,
    speed: 500,
    slidesToShow: Math.min(3, filteredPersonas.length),
    slidesToScroll: 1,
    nextArrow: <NextArrow />,
    prevArrow: <PrevArrow />,
    responsive: [
      {
        breakpoint: 1536,
        settings: {
          slidesToShow: Math.min(3, filteredPersonas.length),
          slidesToScroll: 1,
        }
      },
      {
        breakpoint: 1280,
        settings: {
          slidesToShow: Math.min(2, filteredPersonas.length),
          slidesToScroll: 1,
        }
      },
      {
        breakpoint: 768,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        }
      }
    ]
  };

  if (filteredPersonas.length === 0) {
    return (
      <div className="w-full max-w-[1920px] mx-auto space-y-6 px-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="mb-2">Personas</h1>
            <p className="text-muted-foreground">
              No personas found for this project. Generate some to get started.
            </p>
          </div>
          <Button 
            onClick={() => setShowPersonaWizard(true)}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Generate Personas
          </Button>
        </div>

        <PersonaGenerationWizard
          open={showPersonaWizard}
          onOpenChange={setShowPersonaWizard}
          onGenerate={handleGeneratePersonas}
        />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1920px] mx-auto space-y-8 px-8">
      {/* Header with Filters */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="mb-2">Personas</h1>
          <p className="text-muted-foreground">
            AI-generated customer profiles with behavioral insights
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedProject} onValueChange={setSelectedProject}>
            <SelectTrigger className="w-[280px]">
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              {mockProjects.map(project => (
                <SelectItem key={project.id} value={project.id.toString()}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button 
            onClick={() => setShowPersonaWizard(true)}
            className="bg-brand-orange hover:bg-brand-orange/90 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Generate
          </Button>
        </div>
      </div>

      {/* Statistics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Total Personas</p>
                <p className="text-2xl text-brand-orange">{filteredPersonas.length}</p>
              </div>
              <Users className="w-8 h-8 text-brand-orange" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Avg Tech Savviness</p>
              <div className="flex items-center gap-2">
                <Progress value={avgTechSavviness * 10} className="h-2 flex-1" />
                <span className="text-sm text-foreground">{avgTechSavviness.toFixed(1)}/10</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Avg Brand Loyalty</p>
              <div className="flex items-center gap-2">
                <Progress value={avgBrandLoyalty * 10} className="h-2 flex-1" />
                <span className="text-sm text-foreground">{avgBrandLoyalty.toFixed(1)}/10</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Avg Price Sensitivity</p>
              <div className="flex items-center gap-2">
                <Progress value={avgPriceSensitivity * 10} className="h-2 flex-1" />
                <span className="text-sm text-foreground">{avgPriceSensitivity.toFixed(1)}/10</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Personas Carousel */}
      <div className="relative px-12">
        <Slider {...carouselSettings}>
          {filteredPersonas.map((persona) => (
            <div key={persona.id} className="px-3">
              <Card className="bg-card border border-border hover:shadow-xl hover:border-brand-orange/50 transition-all">
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <CardTitle className="text-foreground">{persona.name}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        {persona.age} • {persona.occupation}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="w-fit">{persona.demographics.location}</Badge>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Background */}
                  <div>
                    <p className="text-sm text-foreground leading-relaxed line-clamp-3">
                      {persona.background}
                    </p>
                  </div>

                  {/* Behavior Profiles */}
                  {persona.behaviorProfiles && (
                    <div className="space-y-2 p-3 border border-border rounded-lg bg-muted/20">
                      <p className="text-xs text-muted-foreground mb-2">Behavior Profile</p>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted-foreground">Tech</span>
                            <span className="text-xs text-foreground">{persona.behaviorProfiles.techSavviness}/10</span>
                          </div>
                          <Progress value={persona.behaviorProfiles.techSavviness * 10} className="h-1" />
                        </div>
                        
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted-foreground">Loyalty</span>
                            <span className="text-xs text-foreground">{persona.behaviorProfiles.brandLoyalty}/10</span>
                          </div>
                          <Progress value={persona.behaviorProfiles.brandLoyalty * 10} className="h-1" />
                        </div>
                        
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted-foreground">Price</span>
                            <span className="text-xs text-foreground">{persona.behaviorProfiles.priceSensitivity}/10</span>
                          </div>
                          <Progress value={persona.behaviorProfiles.priceSensitivity * 10} className="h-1" />
                        </div>
                        
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted-foreground">Risk</span>
                            <span className="text-xs text-foreground">{persona.behaviorProfiles.riskTolerance}/10</span>
                          </div>
                          <Progress value={persona.behaviorProfiles.riskTolerance * 10} className="h-1" />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => setSelectedPersona(persona)}
                      className="flex-1"
                    >
                      View Details
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                    <Button 
                      size="sm"
                      onClick={() => handleOpenBehaviorSimulation(persona)}
                      className="flex-1 bg-brand-orange hover:bg-brand-orange/90 text-white"
                    >
                      <Brain className="w-3 h-3 mr-1" />
                      Simulate
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </Slider>
      </div>

      {/* Behavior Simulation Dialog */}
      <Dialog open={showBehaviorSimulation} onOpenChange={setShowBehaviorSimulation}>
        <DialogContent className="max-w-[95vw] w-full lg:max-w-[1000px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-brand-orange" />
              AI Behavior Simulation
            </DialogTitle>
            <DialogDescription>
              {simulationPersona && `Ask any question about how ${simulationPersona.name} would behave`}
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-6 px-1">
              {/* Persona Summary */}
              {simulationPersona && (
                <Card className="bg-muted/30 border border-border">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <p className="text-foreground mb-1">{simulationPersona.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {simulationPersona.age} • {simulationPersona.occupation}
                        </p>
                      </div>
                      {simulationPersona.behaviorProfiles && (
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                          <div className="text-muted-foreground">Tech: <span className="text-foreground">{simulationPersona.behaviorProfiles.techSavviness}/10</span></div>
                          <div className="text-muted-foreground">Loyalty: <span className="text-foreground">{simulationPersona.behaviorProfiles.brandLoyalty}/10</span></div>
                          <div className="text-muted-foreground">Price: <span className="text-foreground">{simulationPersona.behaviorProfiles.priceSensitivity}/10</span></div>
                          <div className="text-muted-foreground">Risk: <span className="text-foreground">{simulationPersona.behaviorProfiles.riskTolerance}/10</span></div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Custom Question */}
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Ask anything about how this persona might behave:</p>
                <Textarea 
                  placeholder="e.g., How would they respond to a subscription model instead of one-time purchase? What would make them switch from a competitor? How price-sensitive are they?"
                  value={customQuestion}
                  onChange={(e) => setCustomQuestion(e.target.value)}
                  className="min-h-[120px] resize-none"
                  disabled={isSimulating}
                />
                <Button
                  onClick={runCustomSimulation}
                  disabled={isSimulating || !customQuestion.trim()}
                  className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Simulate Response
                </Button>
              </div>

              {/* Simulation Result */}
              {isSimulating && (
                <Card className="bg-card border border-brand-orange">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-brand-orange border-t-transparent rounded-full animate-spin" />
                      <p className="text-muted-foreground">Analyzing behavior patterns...</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {simulationResult && !isSimulating && (
                <Card className="bg-card border border-brand-orange">
                  <CardContent className="p-6 space-y-4">
                    {/* Custom Question */}
                    {simulationResult.customQuestion && (
                      <div className="pb-4 border-b border-border">
                        <p className="text-sm text-muted-foreground mb-2">Your Question</p>
                        <p className="text-foreground italic">"{simulationResult.customQuestion}"</p>
                      </div>
                    )}
                    
                    {/* Prediction */}
                    <div>
                      <div className="flex items-start justify-between mb-2">
                        <p className="text-sm text-muted-foreground">Prediction</p>
                        <Badge className="bg-brand-orange text-white">
                          {simulationResult.confidence}% confidence
                        </Badge>
                      </div>
                      <p className="text-foreground">{simulationResult.prediction}</p>
                    </div>

                    {/* Reasoning */}
                    <div>
                      <p className="text-sm text-muted-foreground mb-2">Reasoning</p>
                      <ul className="space-y-2">
                        {simulationResult.reasoning.map((reason: string, index: number) => (
                          <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                            <span className="text-brand-orange mt-1">•</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Recommendation */}
                    <div className="pt-4 border-t border-border">
                      <p className="text-sm text-muted-foreground mb-2">Recommendation</p>
                      <p className="text-sm text-foreground">{simulationResult.recommendation}</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      <PersonaDetailsDrawer
        persona={selectedPersona}
        open={!!selectedPersona}
        onOpenChange={(open) => {
          if (!open) setSelectedPersona(null);
        }}
      />

      <PersonaGenerationWizard
        open={showPersonaWizard}
        onOpenChange={setShowPersonaWizard}
        onGenerate={handleGeneratePersonas}
      />
    </div>
  );
}
