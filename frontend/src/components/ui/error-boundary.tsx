import React, { Component, ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from './button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  translations?: {
    title: string;
    description: string;
    reloadButton: string;
  };
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundaryClass extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const translations = this.props.translations || {
        title: 'Something went wrong',
        description: 'An unexpected error occurred while rendering this component.',
        reloadButton: 'Reload Page',
      };

      return (
        <div className="flex flex-col items-center justify-center h-full p-8">
          <AlertCircle className="w-16 h-16 text-destructive mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">{translations.title}</h3>
          <p className="text-muted-foreground text-center max-w-md mb-4">
            {this.state.error?.message || translations.description}
          </p>
          <Button
            onClick={() => {
              this.setState({ hasError: false, error: undefined });
              window.location.reload();
            }}
          >
            {translations.reloadButton}
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Functional wrapper with i18n support
export function ErrorBoundary({ children, fallback }: Omit<Props, 'translations'>) {
  const { t } = useTranslation('common');

  const translations = {
    title: t('ui.errorBoundary.title'),
    description: t('ui.errorBoundary.description'),
    reloadButton: t('ui.errorBoundary.reloadButton'),
  };

  return (
    <ErrorBoundaryClass translations={translations} fallback={fallback}>
      {children}
    </ErrorBoundaryClass>
  );
}
