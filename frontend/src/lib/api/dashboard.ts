/**
 * Dashboard API Client
 *
 * Wszystkie API calls dla dashboardu używając istniejącego apiClient
 */

import axios from 'axios';
import type {
  OverviewResponse,
  QuickAction,
  ActionExecutionResult,
  ProjectWithHealth,
  WeeklyCompletionData,
  InsightAnalyticsData,
  InsightHighlight,
  InsightDetail,
  HealthBlockersResponse,
  UsageBudgetResponse,
  Notification,
} from '@/types/dashboard';

const baseUrl = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api/v1`
  : '/api/v1';

const api = axios.create({
  baseURL: baseUrl,
});

// Add auth interceptor - attach JWT token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors globally - redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  // Overview
  getOverview: async (): Promise<OverviewResponse> => {
    const { data } = await api.get<OverviewResponse>('/dashboard/overview');
    return data;
  },

  // Quick Actions
  getQuickActions: async (limit: number = 4): Promise<QuickAction[]> => {
    const { data } = await api.get<QuickAction[]>('/dashboard/quick-actions', {
      params: { limit },
    });
    return data;
  },

  executeAction: async (actionId: string): Promise<ActionExecutionResult> => {
    const { data } = await api.post<ActionExecutionResult>(
      `/dashboard/actions/${actionId}/execute`
    );
    return data;
  },

  // Active Projects
  getActiveProjects: async (): Promise<ProjectWithHealth[]> => {
    const { data } = await api.get<ProjectWithHealth[]>('/dashboard/projects/active');
    return data;
  },

  // Analytics
  getWeeklyCompletion: async (weeks: number = 8): Promise<WeeklyCompletionData> => {
    const { data } = await api.get<WeeklyCompletionData>('/dashboard/analytics/weekly', {
      params: { weeks },
    });
    return data;
  },

  getInsightAnalytics: async (): Promise<InsightAnalyticsData> => {
    const { data } = await api.get<InsightAnalyticsData>('/dashboard/analytics/insights');
    return data;
  },

  // Insights
  getLatestInsights: async (limit: number = 10): Promise<InsightHighlight[]> => {
    const { data } = await api.get<InsightHighlight[]>('/dashboard/insights/latest', {
      params: { limit },
    });
    return data;
  },

  getInsightDetail: async (insightId: string): Promise<InsightDetail> => {
    const { data } = await api.get<InsightDetail>(`/dashboard/insights/${insightId}`);
    return data;
  },

  // Health & Blockers
  getHealthBlockers: async (): Promise<HealthBlockersResponse> => {
    const { data } = await api.get<HealthBlockersResponse>('/dashboard/health/blockers');
    return data;
  },

  // Usage & Budget
  getUsageBudget: async (): Promise<UsageBudgetResponse> => {
    const { data } = await api.get<UsageBudgetResponse>('/dashboard/usage');
    return data;
  },

  // Notifications
  getNotifications: async (
    unreadOnly: boolean = false,
    limit: number = 20
  ): Promise<Notification[]> => {
    const { data } = await api.get<Notification[]>('/dashboard/notifications', {
      params: { unread_only: unreadOnly, limit },
    });
    return data;
  },

  markNotificationRead: async (notificationId: string): Promise<void> => {
    await api.post(`/dashboard/notifications/${notificationId}/read`);
  },

  markNotificationDone: async (notificationId: string): Promise<void> => {
    await api.post(`/dashboard/notifications/${notificationId}/done`);
  },
};
