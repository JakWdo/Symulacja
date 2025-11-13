/**
 * Export API Client
 *
 * HTTP client dla eksportu raportów projektów do PDF i DOCX.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1`
    : '/api/v1',
});

// Auth interceptor - dodaje token do każdego requesta
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// === TYPES ===

export type ExportFormat = 'pdf' | 'docx';

export interface ExportOptions {
  includeFullPersonas?: boolean; // Czy dołączyć wszystkie persony (false = tylko top 10)
}

// === API FUNCTIONS ===

/**
 * Eksportuje raport projektu do PDF.
 *
 * @param projectId - UUID projektu
 * @param options - Opcje eksportu (includeFullPersonas)
 * @returns Blob z plikiem PDF
 */
export async function exportProjectPDF(
  projectId: string,
  options: ExportOptions = {}
): Promise<Blob> {
  const { includeFullPersonas = false } = options;

  const response = await api.get(
    `/export/projects/${projectId}/pdf`,
    {
      params: { include_full_personas: includeFullPersonas },
      responseType: 'blob',
    }
  );

  return response.data;
}

/**
 * Eksportuje raport projektu do DOCX (Microsoft Word).
 *
 * @param projectId - UUID projektu
 * @param options - Opcje eksportu (includeFullPersonas)
 * @returns Blob z plikiem DOCX
 */
export async function exportProjectDOCX(
  projectId: string,
  options: ExportOptions = {}
): Promise<Blob> {
  const { includeFullPersonas = false } = options;

  const response = await api.get(
    `/export/projects/${projectId}/docx`,
    {
      params: { include_full_personas: includeFullPersonas },
      responseType: 'blob',
    }
  );

  return response.data;
}

/**
 * Uniwersalna funkcja eksportu projektu - obsługuje PDF i DOCX.
 *
 * @param projectId - UUID projektu
 * @param format - Format eksportu ('pdf' lub 'docx')
 * @param options - Opcje eksportu
 * @returns Blob z plikiem w wybranym formacie
 */
export async function exportProject(
  projectId: string,
  format: ExportFormat,
  options: ExportOptions = {}
): Promise<Blob> {
  if (format === 'pdf') {
    return exportProjectPDF(projectId, options);
  } else {
    return exportProjectDOCX(projectId, options);
  }
}

/**
 * Pomocnicza funkcja do pobierania pliku w przeglądarce.
 *
 * @param blob - Blob z danymi pliku
 * @param filename - Nazwa pliku do zapisania
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Eksportuje projekt i automatycznie pobiera plik.
 *
 * @param projectId - UUID projektu
 * @param projectName - Nazwa projektu (dla nazwy pliku)
 * @param format - Format eksportu ('pdf' lub 'docx')
 * @param options - Opcje eksportu
 */
export async function exportAndDownload(
  projectId: string,
  projectName: string,
  format: ExportFormat,
  options: ExportOptions = {}
): Promise<void> {
  const blob = await exportProject(projectId, format, options);
  const filename = `projekt_${projectName.replace(/\s+/g, '_')}.${format}`;
  downloadBlob(blob, filename);
}
