import { useTranslation } from 'react-i18next';
import { Logo } from '@/components/ui/logo';

interface AppLoaderProps {
  message?: string;
}

export function AppLoader({ message }: AppLoaderProps) {
  const { t } = useTranslation('common');
  const displayMessage = message || t('status.loading');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-background via-background to-sidebar">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute w-96 h-96 -top-48 -left-48 bg-brand-orange/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute w-96 h-96 -bottom-48 -right-48 bg-chart-1/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* Content */}
      <div className="relative flex flex-col items-center gap-8">
        {/* Logo with spinning animation */}
        <div className="relative">
          <Logo
            spinning
            transparent
            className="w-20 h-20"
          />
          {/* Glow effect ring */}
          <div className="absolute inset-0 rounded-full bg-brand-orange/20 blur-xl animate-glow" />
        </div>

        {/* Loading text */}
        <div className="flex flex-col items-center gap-2">
          <p className="text-lg font-medium text-foreground">{displayMessage}</p>

          {/* Animated dots */}
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-brand-orange rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-brand-orange rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-brand-orange rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  );
}
