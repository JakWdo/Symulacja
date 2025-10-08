import { cn } from '@/lib/utils';

interface SpinnerLogoProps {
  className?: string;
}

export function SpinnerLogo({ className }: SpinnerLogoProps) {
  return (
    <img
      src="/sight-logo-przezroczyste.png"
      alt="Loading"
      className={cn('h-6 w-6 animate-spin', className)}
    />
  );
}
