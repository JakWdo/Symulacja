/**
 * Toast Hook Wrapper
 *
 * Wrapper nad toastStore dla kompatybilności z shadcn/ui API.
 */
import { toast as toastStore } from '@/components/ui/toastStore';

interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
}

/**
 * Toast function - kompatybilny z shadcn/ui API
 */
export function toast(options: ToastOptions) {
  const { title, description, variant, duration } = options;

  if (variant === 'destructive') {
    toastStore.error(title, description, { duration });
  } else {
    toastStore.success(title, description, { duration });
  }
}

/**
 * useToast hook - dla kompatybilności z shadcn/ui
 */
export function useToast() {
  return { toast };
}
