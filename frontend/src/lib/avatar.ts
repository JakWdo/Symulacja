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
 * getAvatarUrl('/static/avatars/abc123.jpg')
 * // => 'http://localhost:8000/static/avatars/abc123.jpg'
 */
export function getAvatarUrl(avatarUrl?: string | null): string | undefined {
  if (!avatarUrl) return undefined;

  // If already a full URL, return as is
  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl;
  }

  // Build full URL from relative path
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
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
