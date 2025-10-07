import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { MoreVertical, Plus, Users, Eye, TrendingUp, BarChart3, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';
import { PersonaGenerationWizard } from './PersonaGenerationWizard';

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
    createdAt: "2024-01-18",
    projectId: 1
  }
];



export function Personas({}: PersonasProps) {
  const [personas, setPersonas] = useState(mockPersonas);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [showPersonaWizard, setShowPersonaWizard] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>("1");
  const [currentPersonaIndex, setCurrentPersonaIndex] = useState(0);
  
  // Filter personas by selected project
  const filteredPersonas = personas.filter(p => p.projectId === parseInt(selectedProject));

  // Calculate population statistics based on filtered personas
  const ageGroups = filteredPersonas.reduce((acc, persona) => {
    const ageGroup = persona.age < 25 ? '18-24' : 
                    persona.age < 35 ? '25-34' : 
                    persona.age < 45 ? '35-44' : 
                    persona.age < 55 ? '45-54' : '55+';
    acc[ageGroup] = (acc[ageGroup] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const genderDistribution = filteredPersonas.reduce((acc, persona) => {
    const gender = persona.demographics.gender;
    acc[gender] = (acc[gender] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topInterests = filteredPersonas.flatMap(p => p.interests)
    .reduce((acc, interest) => {
      acc[interest] = (acc[interest] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

  const sortedInterests = Object.entries(topInterests)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5);

  const handleGeneratePersonas = async (config: any) => {
    // This would integrate with the PersonaGenerationWizard
    console.log('Generating personas with config:', config);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Personas</h1>
          <p className="text-muted-foreground">
            Manage AI-generated and custom personas for your research projects
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedProject} onValueChange={setSelectedProject}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              {mockProjects.map((project) => (
                <SelectItem key={project.id} value={project.id.toString()}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button 
            onClick={() => setShowPersonaWizard(true)}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <Plus className="w-4 h-4 mr-2" />
            Generate Personas
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Personas</p>
                <p className="text-2xl brand-orange">{filteredPersonas.length}</p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Age Range</p>
                <p className="text-2xl brand-orange">
                  {filteredPersonas.length > 0 ? `${Math.min(...filteredPersonas.map(p => p.age))} - ${Math.max(...filteredPersonas.map(p => p.age))}` : 'N/A'}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Top Interest</p>
                <p className="text-2xl brand-orange">
                  {sortedInterests[0]?.[0] || 'N/A'}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Population Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Age Distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(ageGroups).map(([ageGroup, count]) => (
              <div key={ageGroup} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{ageGroup}</span>
                  <span className="text-card-foreground">{count} ({Math.round((count / filteredPersonas.length) * 100)}%)</span>
                </div>
                <Progress value={(count / filteredPersonas.length) * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Top Interests</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sortedInterests.map(([interest, count]) => (
              <div key={interest} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{interest}</span>
                  <span className="text-card-foreground">{count} personas</span>
                </div>
                <Progress value={(count / filteredPersonas.length) * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Persona Carousel */}
      <div className="space-y-4">
        <h2 className="text-xl text-foreground">Design Your Personas</h2>
        
        {filteredPersonas.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Filters Sidebar */}
            <div className="lg:col-span-1">
              <Card className="bg-card border border-border sticky top-6">
                <CardHeader>
                  <CardTitle className="text-card-foreground flex items-center gap-2">
                    <Filter className="w-5 h-5" />
                    Filters & Segments
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Gender Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm">Gender</Label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox id="gender-female" />
                        <label htmlFor="gender-female" className="text-sm text-card-foreground">
                          Female (45%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="gender-male" />
                        <label htmlFor="gender-male" className="text-sm text-card-foreground">
                          Male (40%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="gender-other" />
                        <label htmlFor="gender-other" className="text-sm text-card-foreground">
                          Non-binary (15%)
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Age Range Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm">Age Range</Label>
                    <div className="px-2">
                      <Slider
                        value={[18, 65]}
                        min={18}
                        max={65}
                        step={1}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>18</span>
                        <span>65</span>
                      </div>
                    </div>
                  </div>

                  {/* Occupation Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm">Occupation</Label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-tech" />
                        <label htmlFor="occupation-tech" className="text-sm text-card-foreground">
                          Technology (35%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-healthcare" />
                        <label htmlFor="occupation-healthcare" className="text-sm text-card-foreground">
                          Healthcare (25%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-education" />
                        <label htmlFor="occupation-education" className="text-sm text-card-foreground">
                          Education (20%)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="occupation-business" />
                        <label htmlFor="occupation-business" className="text-sm text-card-foreground">
                          Business (20%)
                        </label>
                      </div>
                    </div>
                  </div>

                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full"
                  >
                    Clear Filters
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Persona Carousel */}
            <div className="lg:col-span-1">
              <Card className="bg-card border border-border">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPersonaIndex(Math.max(0, currentPersonaIndex - 1))}
                        disabled={currentPersonaIndex === 0}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        {currentPersonaIndex + 1} of {filteredPersonas.length}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPersonaIndex(Math.min(filteredPersonas.length - 1, currentPersonaIndex + 1))}
                        disabled={currentPersonaIndex === filteredPersonas.length - 1}
                        className="h-8 w-8 p-0"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    <div className="flex gap-2">
                      {filteredPersonas.map((_, index) => (
                        <button
                          key={index}
                          className={`w-2 h-2 rounded-full transition-colors ${
                            index === currentPersonaIndex ? 'bg-primary' : 'bg-muted'
                          }`}
                          onClick={() => setCurrentPersonaIndex(index)}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Current Persona Card */}
                  {filteredPersonas[currentPersonaIndex] && (
                    <div className="space-y-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-2xl text-card-foreground mb-2">{filteredPersonas[currentPersonaIndex].name}</h3>
                          <p className="text-lg text-muted-foreground">
                            {filteredPersonas[currentPersonaIndex].age} years old • {filteredPersonas[currentPersonaIndex].occupation}
                          </p>
                          <p className="text-muted-foreground">
                            {filteredPersonas[currentPersonaIndex].demographics.location}
                          </p>
                        </div>
                        
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => setSelectedPersona(filteredPersonas[currentPersonaIndex])}>
                              <Eye className="w-4 h-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Users className="w-4 h-4 mr-2" />
                              Duplicate Persona
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>

                      {/* Background */}
                      <div className="space-y-3">
                        <h4 className="text-lg text-card-foreground">Background</h4>
                        <p className="text-muted-foreground leading-relaxed">
                          {filteredPersonas[currentPersonaIndex].background}
                        </p>
                      </div>

                      {/* Demographics Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">Gender</p>
                          <p className="text-card-foreground">{filteredPersonas[currentPersonaIndex].demographics.gender}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">Education</p>
                          <p className="text-card-foreground">{filteredPersonas[currentPersonaIndex].demographics.education}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">Income</p>
                          <p className="text-card-foreground">{filteredPersonas[currentPersonaIndex].demographics.income}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">Lifestyle</p>
                          <p className="text-card-foreground">{filteredPersonas[currentPersonaIndex].psychographics.lifestyle}</p>
                        </div>
                      </div>

                      {/* Interests */}
                      <div className="space-y-3">
                        <h4 className="text-lg text-card-foreground">Interests & Values</h4>
                        <div className="space-y-2">
                          <div>
                            <p className="text-sm text-muted-foreground mb-2">Interests</p>
                            <div className="flex flex-wrap gap-2">
                              {filteredPersonas[currentPersonaIndex].interests.map((interest, index) => (
                                <Badge key={index} variant="secondary" className="bg-primary/10 text-primary border-primary/20">
                                  {interest}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground mb-2">Values</p>
                            <div className="flex flex-wrap gap-2">
                              {filteredPersonas[currentPersonaIndex].psychographics.values.map((value, index) => (
                                <Badge key={index} variant="outline" className="border-secondary text-secondary">
                                  {value}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Creation Date */}
                      <div className="pt-4">
                        <p className="text-xs text-muted-foreground text-right">
                          Created {new Date(filteredPersonas[currentPersonaIndex].createdAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <Card className="bg-card border border-border">
            <CardContent className="p-12 text-center">
              <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg text-card-foreground mb-2">No personas yet</h3>
              <p className="text-muted-foreground mb-4">
                Generate your first AI personas to start understanding your target audience
              </p>
              <Button 
                onClick={() => setShowPersonaWizard(true)}
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                <Plus className="w-4 h-4 mr-2" />
                Generate First Personas
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Persona Detail Dialog */}
      <Dialog open={!!selectedPersona} onOpenChange={() => setSelectedPersona(null)}>
        <DialogContent className="bg-background border border-border text-foreground max-w-4xl max-h-[80vh] overflow-y-auto">
          {selectedPersona && (
            <>
              <DialogHeader>
                <DialogTitle className="text-xl">{selectedPersona.name}</DialogTitle>
                <DialogDescription>
                  Detailed persona profile with demographics, psychographics, and behavioral insights.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Age</p>
                    <p className="text-foreground">{selectedPersona.age} years old</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Occupation</p>
                    <p className="text-foreground">{selectedPersona.occupation}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Location</p>
                    <p className="text-foreground">{selectedPersona.demographics.location}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Income</p>
                    <p className="text-foreground">{selectedPersona.demographics.income}</p>
                  </div>
                </div>
                
                {/* Background */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Background</p>
                  <p className="text-foreground">{selectedPersona.background}</p>
                </div>
                
                {/* Demographics */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Demographics</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Gender</p>
                      <p className="text-foreground">{selectedPersona.demographics.gender}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Education</p>
                      <p className="text-foreground">{selectedPersona.demographics.education}</p>
                    </div>
                  </div>
                </div>
                
                {/* Interests */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Interests</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedPersona.interests.map((interest, idx) => (
                      <Badge key={idx} variant="secondary" className="bg-muted text-muted-foreground">
                        {interest}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                {/* Psychographics */}
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">Psychographics</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Personality</p>
                      <div className="space-y-1">
                        {selectedPersona.psychographics.personality.map((trait, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs mr-1">
                            {trait}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Values</p>
                      <div className="space-y-1">
                        {selectedPersona.psychographics.values.map((value, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs mr-1">
                            {value}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Lifestyle</p>
                      <p className="text-xs text-foreground">{selectedPersona.psychographics.lifestyle}</p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Persona Generation Wizard */}
      <PersonaGenerationWizard
        open={showPersonaWizard}
        onOpenChange={setShowPersonaWizard}
        onGenerate={handleGeneratePersonas}
      />
    </div>
  );
}