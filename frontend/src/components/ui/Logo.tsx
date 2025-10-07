import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  spinning?: boolean;
}

export function Logo({ className, spinning = false }: LogoProps) {
  return (
    <img
      src="/sight-logo-przezroczyste.png"
      alt="Sight logo"
      className={cn(
        'mix-blend-multiply dark:mix-blend-screen',
        spinning && 'animate-spin',
        className
      )}
    />
  );
}
