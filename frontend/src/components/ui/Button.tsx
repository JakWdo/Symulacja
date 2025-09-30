import React from 'react';
import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';

const baseStyles =
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background';

const variantStyles = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700',
  destructive: 'bg-red-500 text-white hover:bg-red-600',
  outline: 'border border-slate-200 bg-transparent hover:bg-slate-100',
  secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200',
  ghost: 'hover:bg-slate-100 hover:text-slate-900',
  link: 'underline-offset-4 hover:underline text-slate-900',
} as const;

const sizeStyles = {
  sm: 'h-9 px-3 rounded-md',
  md: 'h-10 py-2 px-4',
  lg: 'h-11 px-8 rounded-md',
} as const;

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variantStyles;
  size?: keyof typeof sizeStyles;
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        ref={ref}
        disabled={isLoading}
        {...props} // Ta linia została dodana
      >
        {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        {children}
      </button>
    );
  },
);
Button.displayName = 'Button';

export { Button };
