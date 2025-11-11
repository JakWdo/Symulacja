import { api } from './client';
import type {
  GraphQueryResponse,
  RAGDocument,
  RAGQueryRequest,
  RAGQueryResponse,
} from '@/types';

// === RAG API ===
export const ragApi = {
  /**
   * Upload a document to RAG system
   * @param file PDF or DOCX file
   * @param title Document title
   * @param country Country (default: Poland)
   */
  uploadDocument: async (
    file: File,
    title: string,
    country: string = 'Poland'
  ): Promise<RAGDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('country', country);

    const { data } = await api.post<RAGDocument>('/rag/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  /**
   * List all RAG documents
   */
  listDocuments: async (): Promise<RAGDocument[]> => {
    const { data } = await api.get<RAGDocument[]>('/rag/documents');
    return data;
  },

  /**
   * Query RAG system (for testing/preview)
   */
  query: async (request: RAGQueryRequest): Promise<RAGQueryResponse> => {
    const { data } = await api.post<RAGQueryResponse>('/rag/query', request);
    return data;
  },

  /**
   * Delete a RAG document
   */
  deleteDocument: async (documentId: string): Promise<{ message: string }> => {
    const { data } = await api.delete(`/rag/documents/${documentId}`);
    return data;
  },
};

// === GRAPH ANALYSIS API ===
export const graphApi = {
  buildGraph: async (focusGroupId: string): Promise<any> => {
    const { data } = await api.post(`/graph/build/${focusGroupId}`);
    return data;
  },

  getGraph: async (focusGroupId: string, filterType?: string): Promise<any> => {
    const { data } = await api.get(`/graph/${focusGroupId}`, {
      params: { filter_type: filterType }
    });
    return data;
  },

  getInfluentialPersonas: async (focusGroupId: string): Promise<any[]> => {
    const { data } = await api.get(`/graph/${focusGroupId}/influential`);
    return data.personas || [];
  },

  getKeyConcepts: async (focusGroupId: string): Promise<any[]> => {
    const { data } = await api.get(`/graph/${focusGroupId}/concepts`);
    return data.concepts || [];
  },

  getControversialConcepts: async (focusGroupId: string): Promise<any[]> => {
    const { data } = await api.get(`/graph/${focusGroupId}/controversial`);
    return data.controversial_concepts || [];
  },

  getTraitCorrelations: async (focusGroupId: string): Promise<any[]> => {
    const { data } = await api.get(`/graph/${focusGroupId}/correlations`);
    return data.correlations || [];
  },

  getEmotionDistribution: async (focusGroupId: string): Promise<any[]> => {
    const { data } = await api.get(`/graph/${focusGroupId}/emotions`);
    return data.emotions || [];
  },

  askQuestion: async (focusGroupId: string, question: string): Promise<GraphQueryResponse> => {
    const { data } = await api.post(`/graph/${focusGroupId}/ask`, { question });
    return data;
  },
};
