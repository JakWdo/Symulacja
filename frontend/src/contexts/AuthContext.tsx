import React, { createContext, useContext, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, type User, type LoginCredentials, type RegisterData } from '@/lib/api';
import { toast } from '@/components/ui/toastStore';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('access_token')
  );
  const queryClient = useQueryClient();

  // Fetch current user (only if token exists)
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      if (!token) return null;
      try {
        return await authApi.me();
      } catch (error) {
        // Token invalid, clear it
        localStorage.removeItem('access_token');
        setToken(null);
        return null;
      }
    },
    enabled: !!token,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      toast.success('Welcome back!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Login failed');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      toast.success('Account created successfully!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Registration failed');
    },
  });

  // Logout
  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    queryClient.clear();
    toast.info('Logged out');
  };

  const value: AuthContextType = {
    user: user || null,
    isLoading: isLoading || loginMutation.isPending || registerMutation.isPending,
    isAuthenticated: !!user,
    login: async (credentials) => {
      await loginMutation.mutateAsync(credentials);
    },
    register: async (data) => {
      await registerMutation.mutateAsync(data);
    },
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
