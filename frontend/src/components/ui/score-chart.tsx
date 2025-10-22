interface ScoreChartProps {
  score?: number;
  maxScore?: number;
}

export function ScoreChart({ score = 70, maxScore = 100 }: ScoreChartProps) {
  const radius = 100;
  const strokeWidth = 16;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDasharray = `${circumference} ${circumference}`;
  const percentage = (score / maxScore) * 100;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-64 h-64 mx-auto">
      <svg className="block w-full h-full transform -rotate-90" viewBox="0 0 200 200">
        {/* Background circle (gray track) */}
        <circle
          cx="100"
          cy="100"
          r={normalizedRadius}
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Progress circle (orange) */}
        <circle
          cx="100"
          cy="100"
          r={normalizedRadius}
          stroke="#F27405"
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      
      {/* Score text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <span className="text-4xl font-semibold text-card-foreground">{score}</span>
          <span className="text-2xl text-muted-foreground">/{maxScore}</span>
        </div>
      </div>
    </div>
  );
}
