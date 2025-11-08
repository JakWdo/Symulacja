/**
 * Template Metadata - statyczne metadane dla workflow templates
 *
 * Zawiera ikony, czasy wykonania, tagi i kategorie dla 6 gotowych szablonów.
 */

import {
  Microscope,
  Layers,
  RefreshCw,
  Heart,
  Map,
  ListChecks,
  LucideIcon
} from 'lucide-react';

export type TemplateCategory = 'research' | 'analysis' | 'validation';

export interface TemplateMetadata {
  icon: LucideIcon;
  estimatedTime: string;
  tags: string[];
  category: TemplateCategory;
  color: string; // Border/accent color
}

/**
 * Metadata dla 6 predefiniowanych szablonów workflow
 */
export const TEMPLATE_METADATA: Record<string, TemplateMetadata> = {
  'basic_research': {
    icon: Microscope,
    estimatedTime: '~30 min',
    tags: ['Research', 'Quick Start'],
    category: 'research',
    color: '#3b82f6', // blue
  },
  'deep_dive': {
    icon: Layers,
    estimatedTime: '~60 min',
    tags: ['Deep Analysis', 'Comprehensive'],
    category: 'research',
    color: '#8b5cf6', // purple
  },
  'iterative_validation': {
    icon: RefreshCw,
    estimatedTime: '~45 min',
    tags: ['Iterative', 'Validation'],
    category: 'validation',
    color: '#10b981', // green
  },
  'brand_perception': {
    icon: Heart,
    estimatedTime: '~40 min',
    tags: ['Brand', 'Perception'],
    category: 'analysis',
    color: '#ec4899', // pink
  },
  'user_journey': {
    icon: Map,
    estimatedTime: '~50 min',
    tags: ['Journey', 'UX'],
    category: 'analysis',
    color: '#f59e0b', // amber
  },
  'feature_prioritization': {
    icon: ListChecks,
    estimatedTime: '~35 min',
    tags: ['Prioritization', 'Decision'],
    category: 'analysis',
    color: '#14b8a6', // teal
  },
};

/**
 * Helper - pobiera metadata dla template
 */
export function getTemplateMetadata(templateId: string): TemplateMetadata | undefined {
  return TEMPLATE_METADATA[templateId];
}

/**
 * Category labels dla UI
 */
export const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  research: 'Research',
  analysis: 'Analysis',
  validation: 'Validation',
};

/**
 * Workflow Templates dla tabs UI (Figma design)
 */
export interface WorkflowTemplateCard {
  id: string;
  name: string;
  description: string;
  category?: string;
  nodeCount: number;
}

export const workflowTemplates: WorkflowTemplateCard[] = [
  {
    id: 'product-research',
    name: 'Product Research Flow',
    description: 'Complete product research workflow with personas, surveys, and analysis',
    category: 'Product',
    nodeCount: 6,
  },
  {
    id: 'quick-survey',
    name: 'Quick Survey Flow',
    description: 'Simple survey-based research workflow',
    category: 'Survey',
    nodeCount: 3,
  },
  {
    id: 'brand-perception',
    name: 'Brand Perception Study',
    description: 'Understand how customers perceive your brand',
    category: 'Brand',
    nodeCount: 5,
  },
  {
    id: 'user-journey',
    name: 'User Journey Mapping',
    description: 'Map and optimize user experience journey',
    category: 'UX',
    nodeCount: 6,
  },
  {
    id: 'competitive-analysis',
    name: 'Competitive Analysis',
    description: 'Analyze competitors and market positioning',
    category: 'Market',
    nodeCount: 5,
  },
  {
    id: 'feature-prioritization',
    name: 'Feature Prioritization',
    description: 'Prioritize product features based on user feedback',
    category: 'Product',
    nodeCount: 6,
  },
];
