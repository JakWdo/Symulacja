/**
 * Score Chart Component
 * Migrated from sight/src/components/ScoreChart.tsx
 * 
 * Displays a circular progress chart for scores/metrics
 */

export interface ScoreChartProps {
  score: number;
  maxScore?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  label?: string;
  color?: string;
}

/**
 * CircularScoreChart Component
 * 
 * A circular progress indicator showing a score out of a maximum value
 */
export function ScoreChart({
  score,
  maxScore = 100,
  size = 'md',
  showLabel = true,
  label,
  color = '#F27405', // Brand orange
}: ScoreChartProps) {
  // Calculate percentage
  const percentage = Math.min((score / maxScore) * 100, 100);

  // Size configurations
  const sizeConfig = {
    sm: { radius: 60, strokeWidth: 12, textSize: 'text-2xl', subTextSize: 'text-lg' },
    md: { radius: 100, strokeWidth: 16, textSize: 'text-4xl', subTextSize: 'text-2xl' },
    lg: { radius: 140, strokeWidth: 20, textSize: 'text-5xl', subTextSize: 'text-3xl' },
  };

  const config = sizeConfig[size];
  const normalizedRadius = config.radius - config.strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDasharray = `${circumference} ${circumference}`;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const viewBoxSize = config.radius * 2;
  const center = config.radius;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: viewBoxSize, height: viewBoxSize }}>
        <svg
          className="block w-full h-full transform -rotate-90"
          viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
        >
          {/* Background circle (gray track) */}
          <circle
            cx={center}
            cy={center}
            r={normalizedRadius}
            stroke="hsl(var(--muted))"
            strokeWidth={config.strokeWidth}
            fill="transparent"
          />
          
          {/* Progress circle (colored) */}
          <circle
            cx={center}
            cy={center}
            r={normalizedRadius}
            stroke={color}
            strokeWidth={config.strokeWidth}
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Score text overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <span className={`${config.textSize} font-semibold text-card-foreground`}>
              {Math.round(score)}
            </span>
            <span className={`${config.subTextSize} text-muted-foreground`}>
              /{maxScore}
            </span>
          </div>
        </div>
      </div>

      {/* Optional label */}
      {showLabel && label && (
        <span className="text-sm text-muted-foreground text-center">{label}</span>
      )}
    </div>
  );
}

/**
 * Multi-Score Chart Component
 * 
 * Displays multiple scores in a grid layout
 */
export interface MultiScoreChartProps {
  scores: {
    label: string;
    value: number;
    maxValue?: number;
    color?: string;
  }[];
  columns?: 2 | 3 | 4;
}

export function MultiScoreChart({ scores, columns = 3 }: MultiScoreChartProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };

  return (
    <div className={`grid ${gridCols[columns]} gap-6`}>
      {scores.map((score, index) => (
        <ScoreChart
          key={index}
          score={score.value}
          maxScore={score.maxValue}
          label={score.label}
          color={score.color}
          size="sm"
          showLabel={true}
        />
      ))}
    </div>
  );
}

/**
 * Percentage Ring Component
 * Simplified version for displaying just percentages
 */
export interface PercentageRingProps {
  percentage: number;
  label?: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function PercentageRing({
  percentage,
  label,
  color = '#F27405',
  size = 'md',
}: PercentageRingProps) {
  return (
    <ScoreChart
      score={percentage}
      maxScore={100}
      label={label}
      color={color}
      size={size}
      showLabel={!!label}
    />
  );
}

