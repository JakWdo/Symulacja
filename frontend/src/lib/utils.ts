import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { getPersonalityColor as getPersonalityColorFromConstants } from '@/constants/ui';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString();
}

export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString();
}

// Re-export from constants for backward compatibility
export { getPersonalityColorFromConstants as getPersonalityColor };
