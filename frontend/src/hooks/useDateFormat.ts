import { useTranslation } from 'react-i18next';

/**
 * Hook for locale-aware date formatting
 * Automatically uses the correct locale based on current i18n language
 */
export function useDateFormat() {
  const { i18n } = useTranslation();

  /**
   * Format a date string or Date object with locale-aware formatting
   * @param dateString - Date string or Date object to format
   * @param options - Intl.DateTimeFormat options (optional)
   * @returns Formatted date string
   */
  const formatDate = (
    dateString: string | Date,
    options?: Intl.DateTimeFormatOptions
  ): string => {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    const locale = i18n.language === 'pl' ? 'pl-PL' : 'en-US';

    const defaultOptions: Intl.DateTimeFormatOptions = {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    };

    return new Intl.DateTimeFormat(locale, options || defaultOptions).format(date);
  };

  /**
   * Format date as short format (e.g., "Oct 31, 2025" or "31 paź 2025")
   * @param dateString - Date string or Date object to format
   * @returns Short formatted date string
   */
  const formatDateShort = (dateString: string | Date): string => {
    return formatDate(dateString, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  /**
   * Format date with time (e.g., "Oct 31, 2025, 2:30 PM" or "31 paź 2025, 14:30")
   * @param dateString - Date string or Date object to format
   * @returns Formatted date with time string
   */
  const formatDateTime = (dateString: string | Date): string => {
    return formatDate(dateString, {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /**
   * Format date as relative time (e.g., "5 mins ago", "2 hours ago", "3 days ago")
   * @param dateString - Date string or Date object to format
   * @returns Relative time string
   */
  const formatRelativeTime = (dateString: string | Date): string => {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return i18n.language === 'pl' ? 'przed chwilą' : 'just now';
    } else if (diffMins < 60) {
      return i18n.language === 'pl'
        ? `${diffMins} min temu`
        : `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return i18n.language === 'pl'
        ? `${diffHours} godz. temu`
        : `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return i18n.language === 'pl'
        ? `${diffDays} dni temu`
        : `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else {
      // For older dates, show the full date
      return formatDateShort(date);
    }
  };

  /**
   * Format time only (e.g., "2:30 PM" or "14:30")
   * @param dateString - Date string or Date object to format
   * @returns Formatted time string
   */
  const formatTime = (dateString: string | Date): string => {
    return formatDate(dateString, {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return {
    formatDate,
    formatDateShort,
    formatDateTime,
    formatRelativeTime,
    formatTime,
  };
}
