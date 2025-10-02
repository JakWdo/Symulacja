/**
 * PersonaGenerationWizard
 * 5-step wizard for creating personas with custom distributions
 */

import { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Sparkles, Users, MapPin, Brain, Briefcase, Check } from 'lucide-react';
import { DistributionBuilder } from './DistributionBuilder';
import { DEMOGRAPHIC_PRESETS } from '@/lib/demographicPresets';
import type { PersonaAdvancedOptions } from '@/lib/api';

interface PersonaGenerationWizardProps {
  onSubmit: (config: {
    num_personas: number;
    adversarial_mode: boolean;
    advanced_options?: PersonaAdvancedOptions;
  }) => void;
  onCancel: () => void;
  isGenerating: boolean;
}

type WizardStep = 1 | 2 | 3 | 4 | 5;

export function PersonaGenerationWizard({
  onSubmit,
  onCancel,
  isGenerating,
}: PersonaGenerationWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);

  // Step 1: Basic config
  const [numPersonas, setNumPersonas] = useState(10);
  const [adversarialMode, setAdversarialMode] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('balanced');

  // Step 2: Demographics
  const [ageGroups, setAgeGroups] = useState<Record<string, number>>({});
  const [genderWeights, setGenderWeights] = useState<Record<string, number>>({});
  const [educationWeights, setEducationWeights] = useState<Record<string, number>>({});
  const [incomeWeights, setIncomeWeights] = useState<Record<string, number>>({});

  // Step 3: Geography
  const [locationWeights, setLocationWeights] = useState<Record<string, number>>({});
  const [targetCities, setTargetCities] = useState<string>('');
  const [urbanicity, setUrbanicity] = useState<'any' | 'urban' | 'suburban' | 'rural'>('any');

  // Step 4: Psychographics
  const [requiredValues, setRequiredValues] = useState<string>('');
  const [excludedValues, setExcludedValues] = useState<string>('');
  const [requiredInterests, setRequiredInterests] = useState<string>('');
  const [excludedInterests, setExcludedInterests] = useState<string>('');

  // Step 5: Advanced (occupation, personality)
  const [industries, setIndustries] = useState<string>('');
  const [personalitySkew, setPersonalitySkew] = useState<Record<string, number>>({
    openness: 0.5,
    conscientiousness: 0.5,
    extraversion: 0.5,
    agreeableness: 0.5,
    neuroticism: 0.5,
  });

  // Load preset when selected
  const handlePresetChange = (presetId: string) => {
    setSelectedPreset(presetId);
    const preset = DEMOGRAPHIC_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;

    // Apply preset distributions
    if (preset.distributions.custom_age_groups) {
      setAgeGroups(preset.distributions.custom_age_groups);
    }
    if (preset.distributions.gender_weights) {
      setGenderWeights(preset.distributions.gender_weights);
    }
    if (preset.distributions.education_weights) {
      setEducationWeights(preset.distributions.education_weights);
    }
    if (preset.distributions.income_weights) {
      setIncomeWeights(preset.distributions.income_weights);
    }
    if (preset.distributions.location_weights) {
      setLocationWeights(preset.distributions.location_weights);
    }

    // Apply advanced options
    if (preset.advanced_options?.urbanicity) {
      setUrbanicity(preset.advanced_options.urbanicity);
    }
  };

  // Build advanced options object
  const buildAdvancedOptions = useMemo((): PersonaAdvancedOptions | undefined => {
    const options: PersonaAdvancedOptions = {};

    // Demographics
    if (Object.keys(ageGroups).length > 0) {
      options.custom_age_groups = ageGroups;
    }
    if (Object.keys(genderWeights).length > 0) {
      options.gender_weights = genderWeights;
    }
    if (Object.keys(educationWeights).length > 0) {
      options.education_weights = educationWeights;
    }
    if (Object.keys(incomeWeights).length > 0) {
      options.income_weights = incomeWeights;
    }
    if (Object.keys(locationWeights).length > 0) {
      options.location_weights = locationWeights;
    }

    // Geography
    if (targetCities.trim()) {
      options.target_cities = targetCities.split(',').map((c) => c.trim()).filter(Boolean);
    }
    if (urbanicity !== 'any') {
      options.urbanicity = urbanicity;
    }

    // Psychographics
    if (requiredValues.trim()) {
      options.required_values = requiredValues.split(',').map((v) => v.trim()).filter(Boolean);
    }
    if (excludedValues.trim()) {
      options.excluded_values = excludedValues.split(',').map((v) => v.trim()).filter(Boolean);
    }
    if (requiredInterests.trim()) {
      options.required_interests = requiredInterests.split(',').map((i) => i.trim()).filter(Boolean);
    }
    if (excludedInterests.trim()) {
      options.excluded_interests = excludedInterests.split(',').map((i) => i.trim()).filter(Boolean);
    }

    // Advanced
    if (industries.trim()) {
      options.industries = industries.split(',').map((i) => i.trim()).filter(Boolean);
    }

    // Personality skew (only if not all 0.5)
    const hasSkew = Object.values(personalitySkew).some((v) => Math.abs(v - 0.5) > 0.01);
    if (hasSkew) {
      options.personality_skew = personalitySkew;
    }

    return Object.keys(options).length > 0 ? options : undefined;
  }, [
    ageGroups,
    genderWeights,
    educationWeights,
    incomeWeights,
    locationWeights,
    targetCities,
    urbanicity,
    requiredValues,
    excludedValues,
    requiredInterests,
    excludedInterests,
    industries,
    personalitySkew,
  ]);

  const handleNext = () => {
    if (currentStep < 5) {
      setCurrentStep((currentStep + 1) as WizardStep);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((currentStep - 1) as WizardStep);
    }
  };

  const handleSubmit = () => {
    onSubmit({
      num_personas: numPersonas,
      adversarial_mode: adversarialMode,
      advanced_options: buildAdvancedOptions,
    });
  };

  const steps = [
    { number: 1, title: 'Basic Setup', icon: Users },
    { number: 2, title: 'Demographics', icon: Users },
    { number: 3, title: 'Geography', icon: MapPin },
    { number: 4, title: 'Psychographics', icon: Brain },
    { number: 5, title: 'Advanced', icon: Briefcase },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Persona Generation Wizard
          </h2>
          <p className="text-purple-100 text-xs mt-1">
            Create custom personas with precise demographic control
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-slate-50">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isActive = currentStep === step.number;
            const isCompleted = currentStep > step.number;

            return (
              <div key={step.number} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                      isActive
                        ? 'bg-purple-600 text-white shadow-lg scale-110'
                        : isCompleted
                        ? 'bg-green-500 text-white'
                        : 'bg-slate-200 text-slate-400'
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>
                  <span
                    className={`text-[10px] mt-1 font-medium ${
                      isActive ? 'text-purple-600' : isCompleted ? 'text-green-600' : 'text-slate-400'
                    }`}
                  >
                    {step.title}
                  </span>
                </div>
                {idx < steps.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 mx-2 transition-all ${
                      isCompleted ? 'bg-green-500' : 'bg-slate-200'
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {currentStep === 1 && (
            <Step1BasicSetup
              numPersonas={numPersonas}
              setNumPersonas={setNumPersonas}
              adversarialMode={adversarialMode}
              setAdversarialMode={setAdversarialMode}
              selectedPreset={selectedPreset}
              onPresetChange={handlePresetChange}
            />
          )}
          {currentStep === 2 && (
            <Step2Demographics
              ageGroups={ageGroups}
              setAgeGroups={setAgeGroups}
              genderWeights={genderWeights}
              setGenderWeights={setGenderWeights}
              educationWeights={educationWeights}
              setEducationWeights={setEducationWeights}
              incomeWeights={incomeWeights}
              setIncomeWeights={setIncomeWeights}
            />
          )}
          {currentStep === 3 && (
            <Step3Geography
              locationWeights={locationWeights}
              setLocationWeights={setLocationWeights}
              targetCities={targetCities}
              setTargetCities={setTargetCities}
              urbanicity={urbanicity}
              setUrbanicity={setUrbanicity}
            />
          )}
          {currentStep === 4 && (
            <Step4Psychographics
              requiredValues={requiredValues}
              setRequiredValues={setRequiredValues}
              excludedValues={excludedValues}
              setExcludedValues={setExcludedValues}
              requiredInterests={requiredInterests}
              setRequiredInterests={setRequiredInterests}
              excludedInterests={excludedInterests}
              setExcludedInterests={setExcludedInterests}
            />
          )}
          {currentStep === 5 && (
            <Step5Advanced
              industries={industries}
              setIndustries={setIndustries}
              personalitySkew={personalitySkew}
              setPersonalitySkew={setPersonalitySkew}
            />
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 px-4 py-2.5 bg-slate-50 flex items-center justify-between">
          <button
            onClick={onCancel}
            disabled={isGenerating}
            className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800 font-medium disabled:opacity-50"
          >
            Cancel
          </button>
          <div className="flex gap-2">
            {currentStep > 1 && (
              <button
                onClick={handleBack}
                disabled={isGenerating}
                className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 flex items-center gap-1.5 disabled:opacity-50"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Back
              </button>
            )}
            {currentStep < 5 ? (
              <button
                onClick={handleNext}
                className="px-4 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-1.5"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isGenerating}
                className="px-4 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-1.5 disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Generate Personas
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Step 1: Basic Setup
function Step1BasicSetup({
  numPersonas,
  setNumPersonas,
  adversarialMode,
  setAdversarialMode,
  selectedPreset,
  onPresetChange,
}: any) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold text-slate-900 mb-3">Basic Configuration</h3>

        {/* Number of personas */}
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-slate-700">
            Number of Personas
          </label>
          <input
            type="number"
            min="2"
            max="100"
            value={numPersonas}
            onChange={(e) => setNumPersonas(parseInt(e.target.value, 10))}
            className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <p className="text-xs text-slate-500">
            Generate between 2-100 personas (more = slower but more diverse)
          </p>
        </div>

        {/* Adversarial mode */}
        <div className="mt-3 flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
          <input
            type="checkbox"
            id="adversarial"
            checked={adversarialMode}
            onChange={(e) => setAdversarialMode(e.target.checked)}
            className="w-5 h-5 text-purple-600 border-slate-300 rounded focus:ring-purple-500"
          />
          <label htmlFor="adversarial" className="flex-1">
            <div className="font-medium text-slate-900">Adversarial Mode</div>
            <div className="text-xs text-slate-600">
              Generate challenging personas to stress-test your idea
            </div>
          </label>
        </div>
      </div>

      {/* Preset Templates */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Demographic Preset
        </label>
        <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto pr-2">
          {DEMOGRAPHIC_PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => onPresetChange(preset.id)}
              className={`p-2.5 rounded-lg border-2 text-left transition-all ${
                selectedPreset === preset.id
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-slate-200 bg-white hover:border-purple-300'
              }`}
            >
              <div className="text-xl mb-0.5">{preset.icon}</div>
              <div className="font-semibold text-xs text-slate-900">{preset.name}</div>
              <div className="text-[10px] text-slate-600 mt-0.5 line-clamp-2">{preset.description}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// Step 2: Demographics
function Step2Demographics({
  ageGroups,
  setAgeGroups,
  genderWeights,
  setGenderWeights,
  educationWeights,
  setEducationWeights,
  incomeWeights,
  setIncomeWeights,
}: any) {
  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-base font-semibold text-slate-900">Demographic Distributions</h3>
        <p className="text-xs text-slate-600 mt-1">
          Customize how your personas are distributed across age, gender, education, and income. Sliders must sum to 100%.
        </p>
      </div>

      <DistributionBuilder
        title="Age Groups"
        distribution={ageGroups}
        onChange={setAgeGroups}
        allowCustomCategories
        suggestedCategories={['18-24', '25-34', '35-44', '45-54', '55-64', '65+']}
        colorScheme="#8b5cf6"
      />

      <DistributionBuilder
        title="Gender"
        distribution={genderWeights}
        onChange={setGenderWeights}
        allowCustomCategories
        suggestedCategories={['male', 'female', 'non-binary']}
        colorScheme="#ec4899"
      />

      <DistributionBuilder
        title="Education Level"
        distribution={educationWeights}
        onChange={setEducationWeights}
        allowCustomCategories
        suggestedCategories={['High school', 'Some college', "Bachelor's degree", "Master's degree", 'Doctorate']}
        colorScheme="#3b82f6"
      />

      <DistributionBuilder
        title="Income Bracket"
        distribution={incomeWeights}
        onChange={setIncomeWeights}
        allowCustomCategories
        suggestedCategories={['< $25k', '$25k-$50k', '$50k-$75k', '$75k-$100k', '$100k-$150k', '> $150k']}
        colorScheme="#10b981"
      />
    </div>
  );
}

// Step 3: Geography
function Step3Geography({
  locationWeights,
  setLocationWeights,
  targetCities,
  setTargetCities,
  urbanicity,
  setUrbanicity,
}: any) {
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-slate-900">Geographic Targeting</h3>

      <DistributionBuilder
        title="Location Distribution"
        distribution={locationWeights}
        onChange={setLocationWeights}
        allowCustomCategories
        suggestedCategories={['New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX', 'Phoenix, AZ']}
        colorScheme="#f59e0b"
      />

      <div>
        <label className="block text-xs font-medium text-slate-700 mb-1">
          Target Cities (comma-separated)
        </label>
        <input
          type="text"
          value={targetCities}
          onChange={(e) => setTargetCities(e.target.value)}
          placeholder="e.g., San Francisco, Seattle, Austin"
          className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-slate-700 mb-1">
          Urbanicity Preference
        </label>
        <div className="grid grid-cols-4 gap-1.5">
          {(['any', 'urban', 'suburban', 'rural'] as const).map((option) => (
            <button
              key={option}
              onClick={() => setUrbanicity(option)}
              className={`px-3 py-1.5 rounded-lg border-2 text-xs font-medium transition-all ${
                urbanicity === option
                  ? 'border-purple-500 bg-purple-50 text-purple-700'
                  : 'border-slate-200 text-slate-700 hover:border-purple-300'
              }`}
            >
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// Step 4: Psychographics
function Step4Psychographics({
  requiredValues,
  setRequiredValues,
  excludedValues,
  setExcludedValues,
  requiredInterests,
  setRequiredInterests,
  excludedInterests,
  setExcludedInterests,
}: any) {
  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-base font-semibold text-slate-900">Psychographic Filters</h3>
        <p className="text-xs text-slate-600 mt-1">
          Target specific values and interests. Leave blank for no restrictions.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Required Values
          </label>
          <textarea
            value={requiredValues}
            onChange={(e) => setRequiredValues(e.target.value)}
            placeholder="e.g., Innovation, Sustainability"
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-16 resize-none"
          />
          <p className="text-[10px] text-slate-500 mt-0.5">Comma-separated</p>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Excluded Values
          </label>
          <textarea
            value={excludedValues}
            onChange={(e) => setExcludedValues(e.target.value)}
            placeholder="e.g., Materialism, Risk-taking"
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-16 resize-none"
          />
          <p className="text-[10px] text-slate-500 mt-0.5">Comma-separated</p>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Required Interests
          </label>
          <textarea
            value={requiredInterests}
            onChange={(e) => setRequiredInterests(e.target.value)}
            placeholder="e.g., Technology, Travel"
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-16 resize-none"
          />
          <p className="text-[10px] text-slate-500 mt-0.5">Comma-separated</p>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Excluded Interests
          </label>
          <textarea
            value={excludedInterests}
            onChange={(e) => setExcludedInterests(e.target.value)}
            placeholder="e.g., Gambling, Smoking"
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 h-16 resize-none"
          />
          <p className="text-[10px] text-slate-500 mt-0.5">Comma-separated</p>
        </div>
      </div>
    </div>
  );
}

// Step 5: Advanced
function Step5Advanced({
  industries,
  setIndustries,
  personalitySkew,
  setPersonalitySkew,
}: any) {
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-slate-900">Advanced Options</h3>

      <div>
        <label className="block text-xs font-medium text-slate-700 mb-1">
          Target Industries (comma-separated)
        </label>
        <input
          type="text"
          value={industries}
          onChange={(e) => setIndustries(e.target.value)}
          placeholder="e.g., Technology, Healthcare, Finance"
          className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
      </div>

      <div>
        <h4 className="text-xs font-semibold text-slate-700 mb-1">
          Personality Trait Skew (Big Five)
        </h4>
        <p className="text-[10px] text-slate-600 mb-2">
          Adjust sliders to bias personality traits. 50% = balanced, &lt;50% = low trait, &gt;50% = high trait.
        </p>
        <div className="space-y-2">
          {Object.entries(personalitySkew).map(([trait, value]) => {
            const numValue = typeof value === 'number' ? value : 0.5;
            return (
              <div key={trait} className="space-y-0.5">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-medium text-slate-600 capitalize">
                    {trait}
                  </label>
                  <span className="text-[10px] font-semibold text-slate-700">
                    {(numValue * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={numValue * 100}
                  onChange={(e) =>
                    setPersonalitySkew({
                      ...personalitySkew,
                      [trait]: parseFloat(e.target.value) / 100,
                    })
                  }
                  className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                />
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-2.5">
        <h4 className="text-xs font-semibold text-purple-900 mb-1">Summary</h4>
        <ul className="text-[10px] text-purple-700 space-y-0.5">
          <li>• All distributions will be validated before generation</li>
          <li>• Custom options override preset templates</li>
          <li>• Generation may take 30-60 seconds for large batches</li>
        </ul>
      </div>
    </div>
  );
}
