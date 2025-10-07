export function Logo({ className = '' }: { className?: string }) {
  return (
    <img
      src="/sight-logo.png"
      alt="Sight Logo"
      className={className}
    />
  );
}
