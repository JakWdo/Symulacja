import React from 'react';

interface ResponseCardProps {
  personaName: string;
  personaInitials: string;
  response: string;
  timestamp?: string;
  className?: string;
}

/**
 * Pojedyncza karta odpowiedzi z avatarem persony
 */
export const ResponseCard: React.FC<ResponseCardProps> = React.memo(({
  personaName,
  personaInitials,
  response,
  timestamp,
  className = '',
}) => {
  return (
    <div className={`bg-muted/30 border border-border/50 rounded-figma-inner p-4 space-y-3 ${className}`}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-figma-primary to-figma-secondary rounded-full flex items-center justify-center shrink-0">
          <span className="text-white text-sm font-semibold">{personaInitials}</span>
        </div>
        <div className="flex-1">
          <p className="text-card-foreground font-medium text-sm">{personaName}</p>
          {timestamp && (
            <p className="text-xs text-muted-foreground">
              {new Date(timestamp).toLocaleString('pl-PL', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>
      </div>
      <p className="text-sm text-muted-foreground leading-relaxed ml-13">
        {response || <span className="italic">Brak odpowiedzi</span>}
      </p>
    </div>
  );
});

ResponseCard.displayName = 'ResponseCard';
