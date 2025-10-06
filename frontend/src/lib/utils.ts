import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString();
}

export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString();
}

export function getPersonalityColor(score: number): string {
  if (score >= 0.7) return 'bg-green-100 text-green-700';
  if (score >= 0.4) return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}
