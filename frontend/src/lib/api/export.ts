/**
 * Export API - Eksport raportów do PDF i DOCX
 */
import { api } from './client';

export type ExportFormat = 'pdf' | 'docx';

/**
 * Pomocnicza funkcja do pobierania pliku z API
 */
async function downloadFile(url: string, filename: string): Promise<void> {
  const response = await api.get(url, {
    responseType: 'blob',
  });

  // Utwórz URL blob dla pliku
  const blob = new Blob([response.data], {
    type: response.headers['content-type'] || 'application/octet-stream',
  });
  const blobUrl = window.URL.createObjectURL(blob);

  // Utwórz tymczasowy link i kliknij
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  window.URL.revokeObjectURL(blobUrl);
}

/**
 * Eksportuje raport persony do PDF lub DOCX
 */
export async function exportPersona(
  personaId: number,
  format: ExportFormat,
  includeReasoning: boolean = true
): Promise<void> {
  const url = `/export/personas/${personaId}/${format}?include_reasoning=${includeReasoning}`;
  const filename = `persona_${personaId}.${format}`;
  await downloadFile(url, filename);
}

/**
 * Eksportuje raport grupy fokusowej do PDF lub DOCX
 */
export async function exportFocusGroup(
  focusGroupId: number,
  format: ExportFormat,
  includeDiscussion: boolean = true
): Promise<void> {
  const url = `/export/focus-groups/${focusGroupId}/${format}?include_discussion=${includeDiscussion}`;
  const filename = `focus_group_${focusGroupId}.${format}`;
  await downloadFile(url, filename);
}

/**
 * Eksportuje raport ankiety do PDF lub DOCX
 */
export async function exportSurvey(
  surveyId: number,
  format: ExportFormat
): Promise<void> {
  const url = `/export/surveys/${surveyId}/${format}`;
  const filename = `survey_${surveyId}.${format}`;
  await downloadFile(url, filename);
}
