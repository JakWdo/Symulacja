import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  spinning?: boolean;
}

export function Logo({ className, spinning = false }: LogoProps) {
  // Use transparent logo for spinning animation
  const logoSrc = spinning ? '/sight-logo-przezroczyste.png' : '/logo.png';

  return (
    <img
      src={logoSrc}
      alt="Sight logo"
      className={cn(
        spinning && 'animate-spin',
        className
      )}
    />
  );
}
