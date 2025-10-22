import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  spinning?: boolean;
  transparent?: boolean;
}

export function Logo({ className, spinning = false, transparent = false }: LogoProps) {
  // Use transparent logo for spinning animation or when explicitly requested
  const logoSrc =
    spinning || transparent ? '/sight-logo-przezroczyste.png' : '/logo.png';

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
