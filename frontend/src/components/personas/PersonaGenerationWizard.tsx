import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowRight, ArrowLeft, Users, Target, MapPin, Brain, Settings, ChevronRight, AlertCircle, Check } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PersonaGenerationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerate: (config: PersonaGenerationConfig) => void;
}

export interface PersonaGenerationConfig {
  // Basic Setup
  personaCount: number;
  adversarialMode: boolean;
  demographicPreset: string;
  
  // Demographics
  ageGroups: Record<string, [number]>;
  genderDistribution: Record<string, [number]>;
  educationLevels: Record<string, [number]>;
  incomeBrackets: Record<string, [number]>;
  
  // Geography
  locationDistribution: { city: string; weight: number }[];
  targetCities: string;
  urbanicity: string;
  
  // Psychographics
  requiredValues: string[];
  excludedValues: string[];
  requiredInterests: string[];
  excludedInterests: string[];
  
  // Advanced
  targetIndustries: string[];
  personalitySkew: Record<string, [number]>;
}

const demographicPresets = [
  { id: 'gen-z', name: 'Gen Z Consumers', description: 'Ages 18-27, digital natives, value-conscious' },
  { id: 'millennials', name: 'Millennials', description: 'Ages 28-43, tech-savvy professionals' },
  { id: 'gen-x', name: 'Gen X', description: 'Ages 44-59, established careers, family-focused' },
  { id: 'boomers', name: 'Baby Boomers', description: 'Ages 60+, traditional values, stability-focused' },
  { id: 'tech-pros', name: 'Tech Professionals', description: 'Software engineers, designers, product managers' },
  { id: 'budget-shoppers', name: 'Budget Shoppers', description: 'Price-sensitive, deal-seeking consumers' },
  { id: 'luxury-buyers', name: 'Luxury Buyers', description: 'High-income, quality-focused consumers' },
  { id: 'entrepreneurs', name: 'Entrepreneurs', description: 'Business owners, risk-takers, innovation-focused' },
  { id: 'parents', name: 'Parents', description: 'Families with children, safety and value-conscious' },
  { id: 'students', name: 'Students', description: 'University students, budget-conscious, future-oriented' },
  { id: 'retirees', name: 'Retirees', description: 'Retired individuals, leisure-focused, established' },
  { id: 'urban-prof', name: 'Urban Professionals', description: 'City dwellers, career-focused, convenience-oriented' },
  { id: 'custom', name: 'Custom Configuration', description: 'Create your own demographic distribution' }
];

const personalityTraits = [
  { key: 'openness', name: 'Openness', description: 'Openness to new experiences and ideas' },
  { key: 'conscientiousness', name: 'Conscientiousness', description: 'Organization, discipline, and responsibility' },
  { key: 'extraversion', name: 'Extraversion', description: 'Sociability and outgoing nature' },
  { key: 'agreeableness', name: 'Agreeableness', description: 'Cooperation and trust in others' },
  { key: 'neuroticism', name: 'Neuroticism', description: 'Emotional sensitivity and stress response' }
];

export function PersonaGenerationWizard({ open, onOpenChange, onGenerate }: PersonaGenerationWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [config, setConfig] = useState<PersonaGenerationConfig>({
    // Basic Setup
    personaCount: 20,
    adversarialMode: false,
    demographicPreset: '',
    
    // Demographics
    ageGroups: {
      '18-24': [20],
      '25-34': [30],
      '35-44': [25],
      '45-54': [15],
      '55-64': [7],
      '65+': [3]
    },
    genderDistribution: {
      'male': [45],
      'female': [50],
      'non-binary': [5]
    },
    educationLevels: {
      'high-school': [20],
      'some-college': [25],
      'bachelors': [35],
      'masters': [15],
      'doctorate': [5]
    },
    incomeBrackets: {
      'under-30k': [15],
      '30k-50k': [25],
      '50k-75k': [25],
      '75k-100k': [20],
      '100k-150k': [10],
      'over-150k': [5]
    },
    
    // Geography
    locationDistribution: [
      { city: 'New York City', weight: 30 },
      { city: 'Los Angeles', weight: 25 },
      { city: 'Chicago', weight: 20 },
      { city: 'Houston', weight: 15 },
      { city: 'Phoenix', weight: 10 }
    ],
    targetCities: '',
    urbanicity: 'any',
    
    // Psychographics
    requiredValues: [],
    excludedValues: [],
    requiredInterests: [],
    excludedInterests: [],
    
    // Advanced
    targetIndustries: [],
    personalitySkew: {
      'openness': [50],
      'conscientiousness': [50],
      'extraversion': [50],
      'agreeableness': [50],
      'neuroticism': [50]
    }
  });

  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [newValue, setNewValue] = useState('');
  const [newInterest, setNewInterest] = useState('');
  const [newIndustry, setNewIndustry] = useState('');
  const [newCity, setNewCity] = useState('');
  const [newCityWeight, setNewCityWeight] = useState(10);

  // Calculate distribution totals for validation
  const calculateTotal = (distribution: Record<string, [number]>) => {
    return Object.values(distribution).reduce((sum, [value]) => sum + value, 0);
  };

  const validateStep = (step: number): string[] => {
    const errors: string[] = [];
    
    switch (step) {
      case 1:
        if (config.personaCount < 2 || config.personaCount > 100) {
          errors.push('Number of personas must be between 2 and 100');
        }
        break;
      case 2: {
        const ageTotal = calculateTotal(config.ageGroups);
        const genderTotal = calculateTotal(config.genderDistribution);
        const educationTotal = calculateTotal(config.educationLevels);
        const incomeTotal = calculateTotal(config.incomeBrackets);

        if (Math.abs(ageTotal - 100) > 1) errors.push('Age groups must sum to 100%');
        if (Math.abs(genderTotal - 100) > 1) errors.push('Gender distribution must sum to 100%');
        if (Math.abs(educationTotal - 100) > 1) errors.push('Education levels must sum to 100%');
        if (Math.abs(incomeTotal - 100) > 1) errors.push('Income brackets must sum to 100%');
        break;
      }
      case 3: {
        const locationTotal = config.locationDistribution.reduce((sum, loc) => sum + loc.weight, 0);
        if (config.locationDistribution.length > 0 && Math.abs(locationTotal - 100) > 1) {
          errors.push('Location distribution must sum to 100%');
        }
        break;
      }
    }
    
    return errors;
  };

  const handleNext = () => {
    const errors = validateStep(currentStep);
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    setValidationErrors([]);
    setCurrentStep(prev => Math.min(prev + 1, 5));
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
    setValidationErrors([]);
  };

  const handleGenerate = async () => {
    const allErrors = validateStep(1).concat(validateStep(2), validateStep(3));
    if (allErrors.length > 0) {
      setValidationErrors(allErrors);
      return;
    }
    
    setIsSubmitting(true);
    try {
      onGenerate(config);
      onOpenChange(false);
      // Reset wizard state
      setCurrentStep(1);
      setValidationErrors([]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const applyPreset = (presetId: string) => {
    switch (presetId) {
      case 'gen-z':
        setConfig(prev => ({
          ...prev,
          ageGroups: {
            '18-24': [70],
            '25-34': [30],
            '35-44': [0],
            '45-54': [0],
            '55-64': [0],
            '65+': [0]
          }
        }));
        break;
      case 'millennials':
        setConfig(prev => ({
          ...prev,
          ageGroups: {
            '18-24': [0],
            '25-34': [60],
            '35-44': [40],
            '45-54': [0],
            '55-64': [0],
            '65+': [0]
          }
        }));
        break;
      case 'tech-pros':
        setConfig(prev => ({
          ...prev,
          ageGroups: {
            '18-24': [10],
            '25-34': [50],
            '35-44': [30],
            '45-54': [10],
            '55-64': [0],
            '65+': [0]
          },
          educationLevels: {
            'high-school': [5],
            'some-college': [15],
            'bachelors': [60],
            'masters': [18],
            'doctorate': [2]
          },
          incomeBrackets: {
            'under-30k': [5],
            '30k-50k': [10],
            '50k-75k': [25],
            '75k-100k': [35],
            '100k-150k': [20],
            'over-150k': [5]
          }
        }));
        break;
    }
  };

  const addToList = (list: string[], value: string, setter: (fn: (prev: PersonaGenerationConfig) => PersonaGenerationConfig) => void, key: keyof PersonaGenerationConfig) => {
    if (value.trim() && !list.includes(value.trim())) {
      setter(prev => ({
        ...prev,
        [key]: [...(prev[key] as string[]), value.trim()]
      }));
    }
  };

  const removeFromList = (list: string[], value: string, setter: (fn: (prev: PersonaGenerationConfig) => PersonaGenerationConfig) => void, key: keyof PersonaGenerationConfig) => {
    setter(prev => ({
      ...prev,
      [key]: (prev[key] as string[]).filter(item => item !== value)
    }));
  };

  const addLocation = () => {
    if (newCity.trim() && newCityWeight > 0) {
      const newLocation = { city: newCity.trim(), weight: newCityWeight };
      setConfig(prev => ({
        ...prev,
        locationDistribution: [...prev.locationDistribution, newLocation]
      }));
      setNewCity('');
      setNewCityWeight(10);
    }
  };

  const removeLocation = (index: number) => {
    setConfig(prev => ({
      ...prev,
      locationDistribution: prev.locationDistribution.filter((_, i) => i !== index)
    }));
  };

  const steps = [
    { id: 1, name: 'Basic Setup', icon: Settings },
    { id: 2, name: 'Demographics', icon: Users },
    { id: 3, name: 'Geography', icon: MapPin },
    { id: 4, name: 'Psychographics', icon: Brain },
    { id: 5, name: 'Advanced', icon: Target }
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <Label htmlFor="persona-count" className="text-base font-medium">Number of Personas</Label>
              <p className="text-sm text-muted-foreground mb-3">How many AI personas should be generated? (2-100)</p>
              <Input
                id="persona-count"
                type="number"
                value={config.personaCount}
                onChange={(e) => setConfig(prev => ({ ...prev, personaCount: parseInt(e.target.value) || 20 }))}
                className="bg-input-background border-border"
                min="2"
                max="100"
              />
            </div>



            <Separator />

            <div>
              <Label className="text-base font-medium">Demographic Presets</Label>
              <p className="text-sm text-muted-foreground mb-4">Choose a preset to auto-configure demographics, or select custom</p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {demographicPresets.map((preset) => (
                  <Card 
                    key={preset.id}
                    className={`cursor-pointer transition-all hover:shadow-elevated ${
                      config.demographicPreset === preset.id 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => {
                      setConfig(prev => ({ ...prev, demographicPreset: preset.id }));
                      if (preset.id !== 'custom') {
                        applyPreset(preset.id);
                      }
                    }}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">{preset.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{preset.description}</p>
                        </div>
                        {config.demographicPreset === preset.id && (
                          <Check className="w-4 h-4 text-primary mt-0.5" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Age Groups Distribution</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {Object.entries(config.ageGroups).map(([group, [value]]) => (
                  <div key={group} className="space-y-2">
                    <div className="flex justify-between">
                      <Label className="text-sm">{group} years</Label>
                      <span className="text-sm text-muted-foreground">{value}%</span>
                    </div>
                    <Slider
                      value={[value]}
                      onValueChange={([newValue]) => setConfig(prev => ({
                        ...prev,
                        ageGroups: { ...prev.ageGroups, [group]: [newValue] }
                      }))}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Total: {calculateTotal(config.ageGroups)}% (should equal 100%)
              </p>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium mb-4">Gender Distribution</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {Object.entries(config.genderDistribution).map(([gender, [value]]) => (
                  <div key={gender} className="space-y-2">
                    <div className="flex justify-between">
                      <Label className="text-sm capitalize">{gender}</Label>
                      <span className="text-sm text-muted-foreground">{value}%</span>
                    </div>
                    <Slider
                      value={[value]}
                      onValueChange={([newValue]) => setConfig(prev => ({
                        ...prev,
                        genderDistribution: { ...prev.genderDistribution, [gender]: [newValue] }
                      }))}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Total: {calculateTotal(config.genderDistribution)}% (should equal 100%)
              </p>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium mb-4">Education Levels</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {Object.entries(config.educationLevels).map(([level, [value]]) => (
                  <div key={level} className="space-y-2">
                    <div className="flex justify-between">
                      <Label className="text-sm">{level.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</Label>
                      <span className="text-sm text-muted-foreground">{value}%</span>
                    </div>
                    <Slider
                      value={[value]}
                      onValueChange={([newValue]) => setConfig(prev => ({
                        ...prev,
                        educationLevels: { ...prev.educationLevels, [level]: [newValue] }
                      }))}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Total: {calculateTotal(config.educationLevels)}% (should equal 100%)
              </p>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium mb-4">Income Brackets</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {Object.entries(config.incomeBrackets).map(([bracket, [value]]) => (
                  <div key={bracket} className="space-y-2">
                    <div className="flex justify-between">
                      <Label className="text-sm">{bracket.replace('-', ' - $').replace('k', ',000').replace('under', 'Under $').replace('over', 'Over $')}</Label>
                      <span className="text-sm text-muted-foreground">{value}%</span>
                    </div>
                    <Slider
                      value={[value]}
                      onValueChange={([newValue]) => setConfig(prev => ({
                        ...prev,
                        incomeBrackets: { ...prev.incomeBrackets, [bracket]: [newValue] }
                      }))}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Total: {calculateTotal(config.incomeBrackets)}% (should equal 100%)
              </p>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Location Distribution</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Configure geographic distribution of your personas by city or region.
              </p>
              
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row gap-2">
                  <Input
                    placeholder="City name (e.g., San Francisco)"
                    value={newCity}
                    onChange={(e) => setNewCity(e.target.value)}
                    className="bg-input-background border-border flex-1"
                  />
                  <Input
                    type="number"
                    placeholder="Weight %"
                    value={newCityWeight}
                    onChange={(e) => setNewCityWeight(parseInt(e.target.value) || 0)}
                    className="bg-input-background border-border w-full sm:w-24"
                    min="1"
                    max="100"
                  />
                  <Button onClick={addLocation} variant="outline" className="border-border w-full sm:w-auto">
                    Add
                  </Button>
                </div>

                <div className="space-y-2">
                  {config.locationDistribution.map((location, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                      <div className="flex items-center gap-3">
                        <MapPin className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium">{location.city}</span>
                        <Badge variant="secondary">{location.weight}%</Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeLocation(index)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>

                {config.locationDistribution.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    Total: {config.locationDistribution.reduce((sum, loc) => sum + loc.weight, 0)}% (should equal 100%)
                  </p>
                )}
              </div>
            </div>

            <Separator />

            <div>
              <Label htmlFor="target-cities" className="text-base font-medium">Target Cities (Optional)</Label>
              <p className="text-sm text-muted-foreground mb-3">
                Specific cities to focus on, separated by commas (e.g., "San Francisco, Seattle, Austin")
              </p>
              <Textarea
                id="target-cities"
                value={config.targetCities}
                onChange={(e) => setConfig(prev => ({ ...prev, targetCities: e.target.value }))}
                className="bg-input-background border-border"
                placeholder="San Francisco, Seattle, Austin, Denver"
                rows={2}
              />
            </div>

            <div>
              <Label className="text-base font-medium">Urbanicity Preference</Label>
              <p className="text-sm text-muted-foreground mb-3">Geographic setting preference for personas</p>
              <Select
                value={config.urbanicity}
                onValueChange={(value) => setConfig(prev => ({ ...prev, urbanicity: value }))}
              >
                <SelectTrigger className="bg-input-background border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any Setting</SelectItem>
                  <SelectItem value="urban">Urban Only</SelectItem>
                  <SelectItem value="suburban">Suburban Only</SelectItem>
                  <SelectItem value="rural">Rural Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Required Values</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Values that personas MUST have (e.g., "Innovation, Sustainability")
              </p>
              
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <Input
                  placeholder="Add a required value..."
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToList(config.requiredValues, newValue, setConfig, 'requiredValues');
                      setNewValue('');
                    }
                  }}
                  className="bg-input-background border-border flex-1"
                />
                <Button 
                  onClick={() => {
                    addToList(config.requiredValues, newValue, setConfig, 'requiredValues');
                    setNewValue('');
                  }}
                  variant="outline"
                  className="border-border w-full sm:w-auto"
                >
                  Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {config.requiredValues.map((value) => (
                  <Badge
                    key={value}
                    variant="default"
                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                    onClick={() => removeFromList(config.requiredValues, value, setConfig, 'requiredValues')}
                  >
                    {value} ×
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-4">Excluded Values</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Values to exclude from personas (e.g., "Materialism, Risk-taking")
              </p>
              
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <Input
                  placeholder="Add an excluded value..."
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToList(config.excludedValues, newValue, setConfig, 'excludedValues');
                      setNewValue('');
                    }
                  }}
                  className="bg-input-background border-border flex-1"
                />
                <Button 
                  onClick={() => {
                    addToList(config.excludedValues, newValue, setConfig, 'excludedValues');
                    setNewValue('');
                  }}
                  variant="outline"
                  className="border-border w-full sm:w-auto"
                >
                  Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {config.excludedValues.map((value) => (
                  <Badge
                    key={value}
                    variant="secondary"
                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                    onClick={() => removeFromList(config.excludedValues, value, setConfig, 'excludedValues')}
                  >
                    {value} ×
                  </Badge>
                ))}
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium mb-4">Required Interests</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Interests personas must have (e.g., "Technology, Travel")
              </p>
              
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <Input
                  placeholder="Add a required interest..."
                  value={newInterest}
                  onChange={(e) => setNewInterest(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToList(config.requiredInterests, newInterest, setConfig, 'requiredInterests');
                      setNewInterest('');
                    }
                  }}
                  className="bg-input-background border-border flex-1"
                />
                <Button 
                  onClick={() => {
                    addToList(config.requiredInterests, newInterest, setConfig, 'requiredInterests');
                    setNewInterest('');
                  }}
                  variant="outline"
                  className="border-border w-full sm:w-auto"
                >
                  Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {config.requiredInterests.map((interest) => (
                  <Badge
                    key={interest}
                    variant="default"
                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                    onClick={() => removeFromList(config.requiredInterests, interest, setConfig, 'requiredInterests')}
                  >
                    {interest} ×
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-4">Excluded Interests</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Interests to exclude (e.g., "Gambling, Smoking")
              </p>
              
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <Input
                  placeholder="Add an excluded interest..."
                  value={newInterest}
                  onChange={(e) => setNewInterest(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToList(config.excludedInterests, newInterest, setConfig, 'excludedInterests');
                      setNewInterest('');
                    }
                  }}
                  className="bg-input-background border-border flex-1"
                />
                <Button 
                  onClick={() => {
                    addToList(config.excludedInterests, newInterest, setConfig, 'excludedInterests');
                    setNewInterest('');
                  }}
                  variant="outline"
                  className="border-border w-full sm:w-auto"
                >
                  Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {config.excludedInterests.map((interest) => (
                  <Badge
                    key={interest}
                    variant="secondary"
                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                    onClick={() => removeFromList(config.excludedInterests, interest, setConfig, 'excludedInterests')}
                  >
                    {interest} ×
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Target Industries</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Professional industries to focus on (e.g., "Technology, Healthcare, Finance")
              </p>
              
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <Input
                  placeholder="Add an industry..."
                  value={newIndustry}
                  onChange={(e) => setNewIndustry(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addToList(config.targetIndustries, newIndustry, setConfig, 'targetIndustries');
                      setNewIndustry('');
                    }
                  }}
                  className="bg-input-background border-border flex-1"
                />
                <Button 
                  onClick={() => {
                    addToList(config.targetIndustries, newIndustry, setConfig, 'targetIndustries');
                    setNewIndustry('');
                  }}
                  variant="outline"
                  className="border-border w-full sm:w-auto"
                >
                  Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {config.targetIndustries.map((industry) => (
                  <Badge
                    key={industry}
                    variant="outline"
                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground border-border"
                    onClick={() => removeFromList(config.targetIndustries, industry, setConfig, 'targetIndustries')}
                  >
                    {industry} ×
                  </Badge>
                ))}
              </div>
            </div>

            <Separator />

            <div>
              <h3 className="text-lg font-medium mb-4">Personality Skew (Big Five)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Adjust personality trait distributions. 50% = balanced, &lt;50% = low trait, &gt;50% = high trait
              </p>

              <div className="space-y-6">
                {personalityTraits.map(({ key, name, description }) => (
                  <div key={key} className="space-y-3">
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <Label className="font-medium">{name}</Label>
                        <span className="text-sm text-muted-foreground">{config.personalitySkew[key][0]}%</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{description}</p>
                    </div>
                    
                    <div className="space-y-2">
                      <Slider
                        value={config.personalitySkew[key]}
                        onValueChange={(value) => setConfig(prev => ({
                          ...prev,
                          personalitySkew: { ...prev.personalitySkew, [key]: value }
                        }))}
                        max={100}
                        step={1}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Low {name.toLowerCase()}</span>
                        <span>Balanced</span>
                        <span>High {name.toLowerCase()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl w-full h-[90vh] max-h-[90vh] bg-background border-border text-foreground flex flex-col p-0">
        <div className="p-6 pb-0">
          <DialogHeader>
            <DialogTitle className="text-xl">AI Persona Generation Wizard</DialogTitle>
            <DialogDescription>
              Create advanced AI personas with precise demographic, geographic, and psychographic control.
            </DialogDescription>
          </DialogHeader>

          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-6 mt-6 overflow-x-auto pb-2">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              
              return (
                <div key={step.id} className="flex items-center flex-shrink-0">
                  <div className={`flex items-center justify-center w-8 h-8 lg:w-10 lg:h-10 rounded-full border-2 transition-colors ${
                    isActive 
                      ? 'border-primary bg-primary text-primary-foreground' 
                      : isCompleted 
                      ? 'border-primary bg-primary/10 text-primary' 
                      : 'border-muted-foreground/30 text-muted-foreground'
                  }`}>
                    {isCompleted ? <Check className="w-4 h-4 lg:w-5 lg:h-5" /> : <Icon className="w-4 h-4 lg:w-5 lg:h-5" />}
                  </div>
                  <div className="ml-2 lg:ml-3 flex-1 min-w-0">
                    <p className={`text-xs lg:text-sm font-medium truncate ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                      {step.name}
                    </p>
                  </div>
                  {index < steps.length - 1 && (
                    <ChevronRight className="w-3 h-3 lg:w-4 lg:h-4 text-muted-foreground mx-2 lg:mx-4 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <Alert className="mb-4 border-destructive/50 bg-destructive/10">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <AlertDescription className="text-destructive">
                <ul className="list-disc list-inside space-y-1">
                  {validationErrors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Step Content - Scrollable */}
        <div className="flex-1 overflow-y-auto px-6">
          {renderStepContent()}
        </div>

        {/* Navigation */}
        <div className="flex flex-col sm:flex-row sm:justify-between gap-3 p-6 pt-4 border-t border-border">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1 || isSubmitting}
            className="border-border w-full sm:w-auto"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>

          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
              className="border-border w-full sm:w-auto order-2 sm:order-1"
            >
              Cancel
            </Button>
            
            {currentStep < 5 ? (
              <Button
                onClick={handleNext}
                disabled={isSubmitting}
                className="bg-primary hover:bg-primary/90 w-full sm:w-auto order-1 sm:order-2"
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleGenerate}
                disabled={isSubmitting}
                className="bg-brand-orange hover:bg-brand-orange/90 text-white w-full sm:w-auto order-1 sm:order-2"
              >
                <Users className="w-4 h-4 mr-2" />
                Generate {config.personaCount} Personas
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
