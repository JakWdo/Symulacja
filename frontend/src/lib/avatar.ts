/**
 * Avatar utilities - helper functions for handling avatar URLs
 */

/**
 * Convert relative avatar URL from backend to full URL
 *
 * @param avatarUrl - Avatar URL from backend (can be relative like /static/avatars/...)
 * @returns Full URL or undefined if no avatar
 *
 * @example
 * // Development:
 * getAvatarUrl('/static/avatars/abc123.jpg')
 * // => 'http://localhost:8000/static/avatars/abc123.jpg' (from VITE_API_BASE_URL)
 *
 * // Production (same-origin deployment):
 * getAvatarUrl('/static/avatars/abc123.jpg')
 * // => 'https://sight-xxx.run.app/static/avatars/abc123.jpg' (from window.location.origin)
 */
export function getAvatarUrl(avatarUrl?: string | null): string | undefined {
  if (!avatarUrl) return undefined;

  // If already a full URL, return as is
  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl;
  }

  // Build full URL from relative path
  // In production (Cloud Run), use same origin as the app
  // In development, use VITE_API_BASE_URL from .env
  const baseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
  return `${baseUrl.replace(/\/$/, '')}${avatarUrl}`;
}

/**
 * Get user initials from full name
 *
 * @param name - User's full name
 * @returns Initials (max 2 characters) or 'U' if no name
 *
 * @example
 * getInitials('John Doe')
 * // => 'JD'
 */
export function getInitials(name?: string): string {
  if (!name) return 'U';

  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}
