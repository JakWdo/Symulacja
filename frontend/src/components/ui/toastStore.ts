import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  actionLabel?: string;
  onAction?: () => void;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));

    if (toast.duration !== Infinity) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }));
      }, toast.duration || 5000);
    }
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));

type ToastOptions = Pick<Toast, 'duration' | 'actionLabel' | 'onAction'>;

export const toast = {
  success: (title: string, message?: string, options?: ToastOptions) => {
    useToastStore.getState().addToast({ type: 'success', title, message, ...options });
  },
  error: (title: string, message?: string, options?: ToastOptions) => {
    useToastStore.getState().addToast({ type: 'error', title, message, ...options });
  },
  info: (title: string, message?: string, options?: ToastOptions) => {
    useToastStore.getState().addToast({ type: 'info', title, message, ...options });
  },
};
