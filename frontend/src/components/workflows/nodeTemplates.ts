/**
 * Node Templates - Predefiniowane typy node dla workflow builder
 *
 * Zawiera konfigurację wszystkich dostępnych typów node:
 * - Planning (goal)
 * - Data Collection (persona, survey, focus-group)
 * - Analysis (analysis, insights)
 * - Logic (decision)
 *
 * @example
 * import { nodeTemplates } from './nodeTemplates';
 * const personaTemplate = nodeTemplates.find(t => t.type === 'persona');
 */

import {
  Target,
  Users,
  FileText,
  MessageSquare,
  Brain,
  BarChart3,
  GitBranch,
} from 'lucide-react';

export interface NodeTemplate {
  type: string;
  label: string;
  description: string;
  icon: any;
  estimatedTime?: string;
  category: 'Planning' | 'Data Collection' | 'Analysis' | 'Logic';
}

/**
 * Dostępne node templates
 */
export const nodeTemplates: NodeTemplate[] = [
  // Planning
  {
    type: 'goal',
    label: 'Research Goal',
    description: 'Define research objectives',
    icon: Target,
    estimatedTime: '15m',
    category: 'Planning',
  },

  // Data Collection
  {
    type: 'persona',
    label: 'Generate Personas',
    description: 'AI persona generation',
    icon: Users,
    estimatedTime: '30m',
    category: 'Data Collection',
  },
  {
    type: 'survey',
    label: 'Survey',
    description: 'Create survey',
    icon: FileText,
    estimatedTime: '2h',
    category: 'Data Collection',
  },
  {
    type: 'focus-group',
    label: 'Focus Group',
    description: 'Run discussion',
    icon: MessageSquare,
    estimatedTime: '90m',
    category: 'Data Collection',
  },

  // Analysis
  {
    type: 'analysis',
    label: 'AI Analysis',
    description: 'Analyze results',
    icon: Brain,
    estimatedTime: '45m',
    category: 'Analysis',
  },
  {
    type: 'insights',
    label: 'Insights',
    description: 'Generate insights',
    icon: BarChart3,
    estimatedTime: '20m',
    category: 'Analysis',
  },

  // Logic
  {
    type: 'decision',
    label: 'Decision Point',
    description: 'Conditional logic',
    icon: GitBranch,
    estimatedTime: '5m',
    category: 'Logic',
  },
];

/**
 * Get node template by type
 */
export function getNodeTemplate(type: string): NodeTemplate | undefined {
  return nodeTemplates.find((t) => t.type === type);
}

/**
 * Get node templates by category
 */
export function getNodeTemplatesByCategory(
  category: NodeTemplate['category']
): NodeTemplate[] {
  return nodeTemplates.filter((t) => t.category === category);
}
