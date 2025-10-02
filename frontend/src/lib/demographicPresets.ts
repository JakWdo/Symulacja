/**
 * Demographic Preset Templates
 * Pre-configured demographic distributions for common target audiences
 */

export interface DemographicPreset {
  id: string;
  name: string;
  description: string;
  icon: string; // emoji
  distributions: {
    custom_age_groups?: Record<string, number>;
    gender_weights?: Record<string, number>;
    education_weights?: Record<string, number>;
    income_weights?: Record<string, number>;
    location_weights?: Record<string, number>;
  };
  advanced_options?: {
    age_focus?: 'balanced' | 'young_adults' | 'experienced_leaders';
    gender_balance?: 'balanced' | 'female_skew' | 'male_skew';
    urbanicity?: 'any' | 'urban' | 'suburban' | 'rural';
  };
}

export const DEMOGRAPHIC_PRESETS: DemographicPreset[] = [
  {
    id: 'balanced',
    name: 'Balanced Sample',
    description: 'Representative mix across all demographics',
    icon: '⚖️',
    distributions: {
      custom_age_groups: {
        '18-24': 0.15,
        '25-34': 0.25,
        '35-44': 0.20,
        '45-54': 0.18,
        '55-64': 0.12,
        '65+': 0.10,
      },
      gender_weights: {
        'male': 0.49,
        'female': 0.49,
        'non-binary': 0.02,
      },
      education_weights: {
        'High school': 0.25,
        'Some college': 0.20,
        "Bachelor's degree": 0.30,
        "Master's degree": 0.15,
        'Doctorate': 0.05,
        'Other': 0.05,
      },
      income_weights: {
        '< $25k': 0.15,
        '$25k-$50k': 0.20,
        '$50k-$75k': 0.22,
        '$75k-$100k': 0.18,
        '$100k-$150k': 0.15,
        '> $150k': 0.10,
      },
    },
    advanced_options: {
      age_focus: 'balanced',
      gender_balance: 'balanced',
      urbanicity: 'any',
    },
  },
  {
    id: 'gen_z',
    name: 'Gen Z Focus',
    description: 'Young adults 18-27, tech-savvy, diverse',
    icon: '📱',
    distributions: {
      custom_age_groups: {
        '18-21': 0.35,
        '22-24': 0.40,
        '25-27': 0.25,
      },
      gender_weights: {
        'male': 0.45,
        'female': 0.45,
        'non-binary': 0.10,
      },
      education_weights: {
        'High school': 0.20,
        'Some college': 0.35,
        "Bachelor's degree": 0.35,
        "Master's degree": 0.08,
        'Other': 0.02,
      },
      income_weights: {
        '< $25k': 0.40,
        '$25k-$50k': 0.35,
        '$50k-$75k': 0.20,
        '$75k-$100k': 0.05,
      },
    },
    advanced_options: {
      age_focus: 'young_adults',
      urbanicity: 'urban',
    },
  },
  {
    id: 'millennials',
    name: 'Millennials',
    description: 'Ages 28-43, established careers, families',
    icon: '💼',
    distributions: {
      custom_age_groups: {
        '28-32': 0.30,
        '33-37': 0.35,
        '38-43': 0.35,
      },
      gender_weights: {
        'male': 0.48,
        'female': 0.50,
        'non-binary': 0.02,
      },
      education_weights: {
        'Some college': 0.15,
        "Bachelor's degree": 0.45,
        "Master's degree": 0.30,
        'Doctorate': 0.08,
        'Other': 0.02,
      },
      income_weights: {
        '$25k-$50k': 0.10,
        '$50k-$75k': 0.25,
        '$75k-$100k': 0.30,
        '$100k-$150k': 0.25,
        '> $150k': 0.10,
      },
    },
  },
  {
    id: 'gen_x',
    name: 'Gen X Leaders',
    description: 'Ages 44-59, senior roles, high income',
    icon: '👔',
    distributions: {
      custom_age_groups: {
        '44-49': 0.35,
        '50-54': 0.35,
        '55-59': 0.30,
      },
      gender_weights: {
        'male': 0.55,
        'female': 0.44,
        'non-binary': 0.01,
      },
      education_weights: {
        "Bachelor's degree": 0.35,
        "Master's degree": 0.40,
        'Doctorate': 0.15,
        'Other': 0.10,
      },
      income_weights: {
        '$75k-$100k': 0.20,
        '$100k-$150k': 0.40,
        '> $150k': 0.40,
      },
    },
    advanced_options: {
      age_focus: 'experienced_leaders',
    },
  },
  {
    id: 'baby_boomers',
    name: 'Baby Boomers',
    description: 'Ages 60+, retirees, high net worth',
    icon: '🏖️',
    distributions: {
      custom_age_groups: {
        '60-65': 0.35,
        '66-70': 0.30,
        '71-75': 0.20,
        '76+': 0.15,
      },
      gender_weights: {
        'male': 0.48,
        'female': 0.51,
        'non-binary': 0.01,
      },
      education_weights: {
        'High school': 0.30,
        'Some college': 0.20,
        "Bachelor's degree": 0.30,
        "Master's degree": 0.15,
        'Doctorate': 0.05,
      },
      income_weights: {
        '< $25k': 0.20,
        '$25k-$50k': 0.25,
        '$50k-$75k': 0.20,
        '$75k-$100k': 0.15,
        '$100k-$150k': 0.10,
        '> $150k': 0.10,
      },
    },
  },
  {
    id: 'c_suite',
    name: 'C-Suite Executives',
    description: 'Senior executives, high earners, 40-60',
    icon: '👑',
    distributions: {
      custom_age_groups: {
        '40-45': 0.20,
        '46-50': 0.30,
        '51-55': 0.30,
        '56-60': 0.20,
      },
      gender_weights: {
        'male': 0.65,
        'female': 0.34,
        'non-binary': 0.01,
      },
      education_weights: {
        "Bachelor's degree": 0.25,
        "Master's degree": 0.50,
        'Doctorate': 0.20,
        'Other': 0.05,
      },
      income_weights: {
        '$100k-$150k': 0.15,
        '> $150k': 0.85,
      },
    },
    advanced_options: {
      age_focus: 'experienced_leaders',
    },
  },
  {
    id: 'parents_young_kids',
    name: 'Parents (Young Kids)',
    description: 'Ages 28-45, kids under 12, suburban',
    icon: '👨‍👩‍👧‍👦',
    distributions: {
      custom_age_groups: {
        '28-32': 0.30,
        '33-37': 0.35,
        '38-42': 0.25,
        '43-45': 0.10,
      },
      gender_weights: {
        'male': 0.48,
        'female': 0.50,
        'non-binary': 0.02,
      },
      education_weights: {
        'Some college': 0.20,
        "Bachelor's degree": 0.45,
        "Master's degree": 0.25,
        'Other': 0.10,
      },
      income_weights: {
        '$50k-$75k': 0.25,
        '$75k-$100k': 0.35,
        '$100k-$150k': 0.30,
        '> $150k': 0.10,
      },
    },
    advanced_options: {
      urbanicity: 'suburban',
    },
  },
  {
    id: 'college_students',
    name: 'College Students',
    description: 'Ages 18-24, currently in college',
    icon: '🎓',
    distributions: {
      custom_age_groups: {
        '18-19': 0.25,
        '20-21': 0.35,
        '22-24': 0.40,
      },
      gender_weights: {
        'male': 0.45,
        'female': 0.48,
        'non-binary': 0.07,
      },
      education_weights: {
        'Some college': 0.90,
        "Bachelor's degree": 0.10,
      },
      income_weights: {
        '< $25k': 0.75,
        '$25k-$50k': 0.25,
      },
    },
    advanced_options: {
      age_focus: 'young_adults',
      urbanicity: 'urban',
    },
  },
  {
    id: 'entrepreneurs',
    name: 'Entrepreneurs & Founders',
    description: 'Business owners, 25-50, diverse income',
    icon: '🚀',
    distributions: {
      custom_age_groups: {
        '25-30': 0.25,
        '31-35': 0.30,
        '36-40': 0.25,
        '41-50': 0.20,
      },
      gender_weights: {
        'male': 0.60,
        'female': 0.38,
        'non-binary': 0.02,
      },
      education_weights: {
        'Some college': 0.15,
        "Bachelor's degree": 0.50,
        "Master's degree": 0.30,
        'Other': 0.05,
      },
      income_weights: {
        '< $25k': 0.10,
        '$25k-$50k': 0.15,
        '$50k-$75k': 0.20,
        '$75k-$100k': 0.20,
        '$100k-$150k': 0.20,
        '> $150k': 0.15,
      },
    },
  },
  {
    id: 'healthcare_workers',
    name: 'Healthcare Workers',
    description: 'Medical professionals, 25-55, stable income',
    icon: '⚕️',
    distributions: {
      custom_age_groups: {
        '25-30': 0.20,
        '31-35': 0.25,
        '36-45': 0.35,
        '46-55': 0.20,
      },
      gender_weights: {
        'male': 0.30,
        'female': 0.68,
        'non-binary': 0.02,
      },
      education_weights: {
        "Bachelor's degree": 0.35,
        "Master's degree": 0.40,
        'Doctorate': 0.20,
        'Other': 0.05,
      },
      income_weights: {
        '$50k-$75k': 0.20,
        '$75k-$100k': 0.30,
        '$100k-$150k': 0.35,
        '> $150k': 0.15,
      },
    },
  },
];

/**
 * Get a preset by ID
 */
export function getPresetById(id: string): DemographicPreset | undefined {
  return DEMOGRAPHIC_PRESETS.find((preset) => preset.id === id);
}

/**
 * Get preset names for dropdown
 */
export function getPresetOptions(): Array<{ value: string; label: string; icon: string }> {
  return DEMOGRAPHIC_PRESETS.map((preset) => ({
    value: preset.id,
    label: preset.name,
    icon: preset.icon,
  }));
}
