import { format } from 'date-fns';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value?: string | Date | null, fallback = 'Unknown') {
  if (!value) {
    return fallback;
  }

  try {
    const date = typeof value === 'string' ? new Date(value) : value;
    if (Number.isNaN(date.getTime())) {
      return fallback;
    }

    return format(date, 'dd MMM yyyy');
  } catch (error) {
    console.error('Failed to format date', error);
    return fallback;
  }
}

export function formatTime(milliseconds?: number | null) {
  if (!milliseconds || milliseconds < 0) {
    return '—';
  }

  const seconds = milliseconds / 1000;
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds.toString().padStart(2, '0')}s`;
}

export function formatPercentage(value?: number | null, digits = 1) {
  if (value === undefined || value === null) {
    return '—';
  }

  return `${(value * 100).toFixed(digits)}%`;
}

export function truncateText(text: string | null | undefined, maxLength = 120) {
  if (!text) {
    return '';
  }

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength).trim()}…`;
}

export function getPolarizationLevel(score: number) {
  if (score >= 0.66) {
    return { level: 'High Polarization', color: 'text-red-600' };
  }

  if (score >= 0.33) {
    return { level: 'Moderate Polarization', color: 'text-amber-500' };
  }

  return { level: 'Low Polarization', color: 'text-green-600' };
}

export function generateColorScale(count: number) {
  const colors: string[] = [];

  if (count <= 0) {
    return colors;
  }

  for (let i = 0; i < count; i++) {
    const hue = Math.round((360 / count) * i);
    colors.push(`hsl(${hue} 80% 65%)`);
  }

  return colors;
}

export function getPersonalityColor(label: string, value: number) {
  const normalized = Math.max(0, Math.min(1, value));

  const palette: Record<string, number> = {
    openness: 260,
    conscientiousness: 150,
    extraversion: 35,
    agreeableness: 190,
    neuroticism: 0,
  };

  const hue = palette[label.toLowerCase()] ?? 210;
  const saturation = 70;
  const lightness = 75 - normalized * 20;

  return `hsl(${hue} ${saturation}% ${lightness}%)`;
}
