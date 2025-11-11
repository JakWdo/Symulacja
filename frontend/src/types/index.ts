/**
 * Central Types Export
 *
 * Re-exportuje wszystkie typy z modułów domenowych.
 * Ten plik pozwala na import typów z jednego miejsca: `import { Persona, Project } from '@/types'`
 */

// ============================================================================
// ERROR TYPES (Common)
// ============================================================================

export interface APIError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

// ============================================================================
// DOMAIN EXPORTS
// ============================================================================

// Workflow types
export * from './workflow';

// Persona types
export * from './persona';

// Project types
export * from './project';

// Focus Group types
export * from './focus-group';

// Survey types
export * from './survey';

// RAG types
export * from './rag';

// Graph types
export * from './graph';

// Dashboard types
export * from './dashboard';

// AI Summary types
export * from './ai-summary';

// Persona v2 types (enhanced structure)
export * from './persona_v2';
