/**
 * Teams API Client
 *
 * HTTP client dla Teams endpoints - zarządzanie zespołami i członkami.
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

export type TeamRole = 'owner' | 'member' | 'viewer';

export interface Team {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  member_count?: number;
  project_count?: number;
  members?: TeamMember[];
}

export interface TeamMember {
  user_id: string;
  email: string;
  full_name: string;
  role_in_team: TeamRole;
  joined_at: string;
}

export interface TeamCreate {
  name: string;
  description?: string;
}

export interface TeamUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface TeamMembershipCreate {
  user_id?: string;
  email?: string;
  role_in_team?: TeamRole;
}

export interface TeamMembershipUpdate {
  role_in_team: TeamRole;
}

export interface TeamListResponse {
  teams: Team[];
  total: number;
}

// === API FUNCTIONS ===

/**
 * Tworzy nowy zespół
 *
 * @param data - Dane nowego zespołu (nazwa, opis)
 * @returns Utworzony zespół
 */
export async function createTeam(data: TeamCreate): Promise<Team> {
  const response = await api.post<Team>('/teams', data);
  return response.data;
}

/**
 * Pobiera listę zespołów użytkownika
 *
 * @param skip - Offset dla paginacji
 * @param limit - Liczba zespołów do pobrania
 * @returns Lista zespołów z totalem
 */
export async function getMyTeams(
  skip = 0,
  limit = 100
): Promise<TeamListResponse> {
  const response = await api.get<TeamListResponse>('/teams/my', {
    params: { skip, limit },
  });
  return response.data;
}

/**
 * Pobiera szczegóły zespołu
 *
 * @param teamId - UUID zespołu
 * @returns Szczegóły zespołu z członkami
 */
export async function getTeam(teamId: string): Promise<Team> {
  const response = await api.get<Team>(`/teams/${teamId}`);
  return response.data;
}

/**
 * Aktualizuje dane zespołu
 *
 * @param teamId - UUID zespołu
 * @param data - Dane do aktualizacji
 * @returns Zaktualizowany zespół
 */
export async function updateTeam(
  teamId: string,
  data: TeamUpdate
): Promise<Team> {
  const response = await api.put<Team>(`/teams/${teamId}`, data);
  return response.data;
}

/**
 * Usuwa zespół (soft delete)
 *
 * @param teamId - UUID zespołu
 */
export async function deleteTeam(teamId: string): Promise<void> {
  await api.delete(`/teams/${teamId}`);
}

/**
 * Dodaje członka do zespołu
 *
 * @param teamId - UUID zespołu
 * @param data - Dane członka (user_id lub email, rola)
 * @returns Utworzone członkostwo
 */
export async function addTeamMember(
  teamId: string,
  data: TeamMembershipCreate
): Promise<void> {
  await api.post(`/teams/${teamId}/members`, data);
}

/**
 * Aktualizuje rolę członka zespołu
 *
 * @param teamId - UUID zespołu
 * @param userId - UUID użytkownika
 * @param data - Nowa rola
 */
export async function updateTeamMemberRole(
  teamId: string,
  userId: string,
  data: TeamMembershipUpdate
): Promise<void> {
  await api.put(`/teams/${teamId}/members/${userId}`, data);
}

/**
 * Usuwa członka z zespołu
 *
 * @param teamId - UUID zespołu
 * @param userId - UUID użytkownika
 */
export async function removeTeamMember(
  teamId: string,
  userId: string
): Promise<void> {
  await api.delete(`/teams/${teamId}/members/${userId}`);
}
