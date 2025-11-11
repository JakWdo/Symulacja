/**
 * RAG (Retrieval-Augmented Generation) Types
 *
 * Wszystkie typy związane z systemem RAG, dokumentami i kontekstem.
 */

import type { GraphInsight } from './graph';

// ============================================================================
// RAG DOCUMENTS
// ============================================================================

export interface RAGDocument {
  id: string;
  title: string;
  filename: string;
  file_path: string;
  file_type: 'pdf' | 'docx';
  country: string;
  num_chunks: number;
  status: 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
  is_active: boolean;
}

// ============================================================================
// RAG CITATIONS
// ============================================================================

export interface RAGCitation {
  document_title: string;
  chunk_text: string;
  relevance_score: number;
}

// ============================================================================
// RAG QUERIES
// ============================================================================

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
}

export interface RAGQueryResponse {
  query: string;
  context: string;
  citations: RAGCitation[];
  num_results: number;
}

// ============================================================================
// RAG GRAPH NODES
// ============================================================================

export interface RAGGraphNode {
  type?: string;
  summary?: string;
  streszczenie?: string;
  magnitude?: string;
  skala?: string;
  confidence?: string;
  pewnosc?: string;
  time_period?: string;
  okres_czasu?: string;
  source?: string;
  document_title?: string;
  why_matters?: string;
  kluczowe_fakty?: string;
  [key: string]: unknown;
}

// ============================================================================
// RAG CONTEXT & ORCHESTRATION
// ============================================================================

export interface RagContextOrchestrationReasoning {
  brief?: string;
  graph_insights?: GraphInsight[];
  allocation_reasoning?: string;
  demographics?: Record<string, any>;
  overall_context?: string;
  segment_name?: string;
  segment_description?: string;
  segment_social_context?: string;
  segment_id?: string;
  // NEW: Segment Brief (from SegmentBriefService)
  segment_brief?: {
    segment_id: string;
    segment_name: string;
    description: string; // 400-800 words storytelling
    social_context: string;
    characteristics: string[];
    based_on_personas_count: number;
    demographics: Record<string, any>;
    generated_at: string;
    generated_by: string;
  };
  // NEW: Persona Uniqueness
  persona_uniqueness?: string; // 2-4 sentences about why this persona is unique in segment
}

export interface RagContextDetails {
  search_type?: string;
  num_results?: number;
  graph_nodes_count?: number;
  graph_nodes?: RAGGraphNode[];
  graph_context?: string;
  context_preview?: string;
  context_length?: number;
  enriched_chunks?: number;
  citations_count?: number;
  query?: string;
  orchestration_reasoning?: RagContextOrchestrationReasoning;
}
