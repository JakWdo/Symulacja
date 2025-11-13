/**
 * Environment Selector Component
 *
 * Dropdown do przełączania między environments w topbar.
 * Filtruje environments po aktualnie wybranym teamie.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listEnvironments, type Environment } from '../../api/environments';
import { useTeamStore } from '../../store/teamStore';

interface EnvironmentSelectorProps {
  value: string | null;
  onChange: (environmentId: string) => void;
  className?: string;
}

export const EnvironmentSelector: React.FC<EnvironmentSelectorProps> = ({
  value,
  onChange,
  className = '',
}) => {
  const { currentTeam } = useTeamStore();

  // Fetch environments for current team
  const { data: environments = [], isLoading } = useQuery({
    queryKey: ['environments', currentTeam?.id],
    queryFn: () => listEnvironments(currentTeam?.id),
    enabled: !!currentTeam,
  });

  if (!currentTeam) {
    return null;
  }

  if (isLoading) {
    return (
      <div className={`text-sm text-gray-500 ${className}`}>
        Ładowanie środowisk...
      </div>
    );
  }

  if (environments.length === 0) {
    return (
      <div className={`text-sm text-gray-400 ${className}`}>
        Brak środowisk
      </div>
    );
  }

  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className={`
        px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm
        focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
        text-sm
        ${className}
      `}
    >
      <option value="">Wybierz środowisko</option>
      {environments.map((env) => (
        <option key={env.id} value={env.id}>
          {env.name}
        </option>
      ))}
    </select>
  );
};
