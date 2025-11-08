import React from 'react';

interface NumberedBadgeProps {
  number: number;
  className?: string;
}

/**
 * Okrągły badge z numerem dla Key Insights
 */
export const NumberedBadge: React.FC<NumberedBadgeProps> = ({ number, className = '' }) => {
  return (
    <div
      className={`
        bg-brand rounded-full w-7 h-7
        flex items-center justify-center shrink-0
        ${className}
      `}
    >
      <span className="text-white text-sm font-semibold font-crimson">
        {number}
      </span>
    </div>
  );
};
