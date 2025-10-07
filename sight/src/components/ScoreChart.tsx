import svgPaths from "../imports/svg-x95y8v2itt";

function Group7() {
  const radius = 100;
  const strokeWidth = 16;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDasharray = `${circumference} ${circumference}`;
  const strokeDashoffset = circumference - (70 / 100) * circumference;

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
          <span className="text-4xl font-semibold text-card-foreground">70</span>
          <span className="text-2xl text-muted-foreground">/100</span>
        </div>
      </div>
    </div>
  );
}

function ChartGraphic() {
  return (
    <div className="flex items-center justify-center w-full h-full p-6">
      <Group7 />
    </div>
  );
}

export function ScoreChart() {
  return (
    <div className="w-full h-full flex items-center justify-center" data-name="score-chart">
      <ChartGraphic />
    </div>
  );
}