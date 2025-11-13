/**
 * API Client dla Environments i Shared Context
 *
 * Obsługuje:
 * - Zarządzanie environments (team-level workspaces)
 * - Filtrowanie zasobów (DSL queries)
 * - Saved filters
 * - Project snapshots
 */

import { api } from '../lib/api/client';

// === Types ===

export interface Environment {
  id: string;
  team_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentCreate {
  team_id: string;
  name: string;
  description?: string;
}

export interface FilterResourcesRequest {
  dsl: string;
  resource_type: 'persona' | 'workflow';
  limit?: number;
  cursor?: string;
}

export interface FilterResourcesResponse {
  resource_ids: string[];
  next_cursor: string | null;
  count: number;
}

export interface SavedFilter {
  id: string;
  environment_id: string;
  name: string;
  dsl: string;
  created_by: string | null;
  created_at: string;
}

export interface SavedFilterCreate {
  environment_id: string;
  name: string;
  dsl: string;
}

export interface ProjectSnapshot {
  id: string;
  project_id: string;
  name: string;
  resource_type: 'persona' | 'workflow';
  resource_ids: string[];
  created_at: string;
}

export interface SnapshotCreate {
  name: string;
  resource_type: 'persona' | 'workflow';
}

// === API Functions ===

/**
 * Tworzy nowe environment dla zespołu.
 */
export async function createEnvironment(data: EnvironmentCreate): Promise<Environment> {
  const response = await api.post<Environment>('/environments', data);
  return response.data;
}

/**
 * Listuje environments dostępne dla użytkownika.
 */
export async function listEnvironments(teamId?: string): Promise<Environment[]> {
  const params = teamId ? { team_id: teamId } : {};
  const response = await api.get<Environment[]>('/environments', { params });
  return response.data;
}

/**
 * Pobiera szczegóły environment.
 */
export async function getEnvironment(environmentId: string): Promise<Environment> {
  const response = await api.get<Environment>(`/environments/${environmentId}`);
  return response.data;
}

/**
 * Filtruje zasoby w environment używając DSL query.
 *
 * @example
 * const result = await filterEnvironmentResources(envId, {
 *   dsl: "dem:age-25-34 AND geo:warsaw",
 *   resource_type: "persona",
 *   limit: 50
 * });
 */
export async function filterEnvironmentResources(
  environmentId: string,
  filterRequest: FilterResourcesRequest
): Promise<FilterResourcesResponse> {
  const response = await api.post<FilterResourcesResponse>(
    `/environments/${environmentId}/filter`,
    filterRequest
  );
  return response.data;
}

/**
 * Tworzy nowy saved filter.
 */
export async function createSavedFilter(data: SavedFilterCreate): Promise<SavedFilter> {
  const response = await api.post<SavedFilter>('/environments/filters', data);
  return response.data;
}

/**
 * Listuje saved filters dla environment.
 */
export async function listSavedFilters(environmentId: string): Promise<SavedFilter[]> {
  const response = await api.get<SavedFilter[]>('/environments/filters', {
    params: { environment_id: environmentId }
  });
  return response.data;
}

/**
 * Pobiera szczegóły saved filter.
 */
export async function getSavedFilter(filterId: string): Promise<SavedFilter> {
  const response = await api.get<SavedFilter>(`/environments/filters/${filterId}`);
  return response.data;
}

/**
 * Tworzy snapshot zasobów projektu.
 */
export async function createProjectSnapshot(
  projectId: string,
  data: SnapshotCreate
): Promise<ProjectSnapshot> {
  const response = await api.post<ProjectSnapshot>(
    `/projects/${projectId}/snapshots`,
    data
  );
  return response.data;
}

/**
 * Listuje snapshoty projektu.
 */
export async function listProjectSnapshots(projectId: string): Promise<ProjectSnapshot[]> {
  const response = await api.get<ProjectSnapshot[]>(`/projects/${projectId}/snapshots`);
  return response.data;
}

/**
 * Pobiera szczegóły snapshotu.
 */
export async function getProjectSnapshot(
  projectId: string,
  snapshotId: string
): Promise<ProjectSnapshot> {
  const response = await api.get<ProjectSnapshot>(
    `/projects/${projectId}/snapshots/${snapshotId}`
  );
  return response.data;
}
