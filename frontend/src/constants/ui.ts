/**
 * UI Constants - Centralized UI configuration constants
 *
 * Contains icon standards, UI colors, spacing, and other UI-related constants.
 * Consolidated from:
 * - lib/iconStandards.ts (ICON_STANDARDS)
 */

import {
  Sparkles, // AI general/generation
  Brain, // Deep reasoning/analysis
  Wand2, // Content generation/magic
  Zap, // Speed/automation/energy
  Database, // Data/storage
  Users, // People/personas
  MessageSquare, // Chat/discussion
  FileText, // Documents/surveys
  BarChart3, // Analytics/metrics
  Settings, // Configuration
  AlertCircle, // Warning/error
  CheckCircle, // Success/completed
  Info, // Information
  Loader2, // Loading/progress
} from 'lucide-react';

/**
 * Standardowe ikony używane w aplikacji Sight.
 *
 * Użycie:
 * ```tsx
 * import { ICON_STANDARDS } from '@/constants/ui';
 *
 * <ICON_STANDARDS.ai.general className="w-4 h-4" />
 * ```
 */
export const ICON_STANDARDS = {
  /** Ikony AI/LLM */
  ai: {
    general: Sparkles, // Główna ikona AI (summary, RAG, profile generation)
    reasoning: Brain, // Głęboka analiza/rozumowanie (reasoning panel tylko!)
    generation: Wand2, // Generowanie treści
    automation: Zap, // Automatyzacja/szybkość
  },

  /** Ikony danych */
  data: {
    storage: Database,
    analytics: BarChart3,
  },

  /** Ikony użytkowników */
  users: {
    personas: Users,
  },

  /** Ikony komunikacji */
  communication: {
    discussion: MessageSquare,
    document: FileText,
  },

  /** Ikony systemowe */
  system: {
    settings: Settings,
    loading: Loader2,
  },

  /** Ikony statusu */
  status: {
    warning: AlertCircle,
    success: CheckCircle,
    info: Info,
  },
} as const;

/**
 * Type helper dla icon props
 */
export type IconComponent = typeof ICON_STANDARDS.ai.general;
