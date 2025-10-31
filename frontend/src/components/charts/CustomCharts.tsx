/**
 * Custom Charts Components
 * Migrated from sight/src/components/Dashboard.tsx
 *
 * Provides CustomBarChart and CustomPieChart with dynamic data support
 */

import { useTranslation } from 'react-i18next';
import { pieSvgPaths } from '@/lib/svg-paths';

export interface MonthlyActivity {
  name: string;
  personas: number;
  surveys: number;
  focusGroups: number;
}

export interface CustomBarChartProps {
  data: MonthlyActivity[];
  maxHeight?: number;
}

/**
 * Custom Bar Chart Component
 * 
 * Displays stacked bar chart for monthly activity metrics
 * (personas, surveys, focus groups)
 */
export function CustomBarChart({ data, maxHeight = 200 }: CustomBarChartProps) {
  const { t } = useTranslation('charts');

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-muted-foreground">
        <p>{t('noData')}</p>
      </div>
    );
  }

  return (
    <div className="flex gap-[12px] items-end justify-between relative w-full h-[240px] px-4">
      {data.map((month) => {
        const totalHeight = maxHeight;
        const maxPersonas = Math.max(...data.map((m) => m.personas));
        const maxSurveys = Math.max(...data.map((m) => m.surveys));
        const maxFocusGroups = Math.max(...data.map((m) => m.focusGroups));

        const personasHeight = Math.max(
          20,
          (month.personas / maxPersonas) * (totalHeight * 0.7)
        );
        const surveysHeight = Math.max(
          12,
          (month.surveys / maxSurveys) * (totalHeight * 0.4)
        );
        const focusGroupsHeight = Math.max(
          8,
          (month.focusGroups / maxFocusGroups) * (totalHeight * 0.3)
        );

        return (
          <div key={month.name} className="flex flex-col items-center gap-3">
            <div
              className="bg-[#f3f3f3] flex flex-col items-center justify-end overflow-hidden relative rounded-[5px] w-[38px]"
              style={{ height: `${totalHeight}px` }}
            >
              <div className="flex-1 bg-[#f2f2f2] w-full" />
              <div
                className="bg-[#F27405] w-full"
                style={{ height: `${personasHeight}px` }}
                title={`Personas: ${month.personas}`}
              />
              <div
                className="bg-[#F29F05] w-full"
                style={{ height: `${surveysHeight}px` }}
                title={`Surveys: ${month.surveys}`}
              />
              <div
                className="bg-[#28a745] w-full"
                style={{ height: `${focusGroupsHeight}px` }}
                title={`Focus Groups: ${month.focusGroups}`}
              />
            </div>
            <span className="text-sm text-muted-foreground">{month.name}</span>
          </div>
        );
      })}
    </div>
  );
}

export interface ProjectDistribution {
  name: string;
  value: number;
  color: string;
}

export interface CustomPieChartProps {
  data: ProjectDistribution[];
}

/**
 * Custom Pie Chart Component
 * 
 * Displays pie chart using SVG paths from sight/imports
 * Shows project distribution percentages
 */
export function CustomPieChart({ data }: CustomPieChartProps) {
  const { t } = useTranslation('charts');

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center w-full h-[200px] text-muted-foreground">
        <p>{t('noData')}</p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center w-full">
      <div className="relative size-[140px] mx-auto">
        {/* Background circle */}
        <div className="absolute inset-0">
          <svg
            className="block size-full"
            fill="none"
            preserveAspectRatio="none"
            viewBox="0 0 163 163"
          >
            <path d={pieSvgPaths.p3f58c00} fill="#F5F5F5" />
          </svg>
        </div>

        {/* Pie segments - using SVG paths from sight */}
        {/* Segment 1 - Bottom half */}
        <div className="absolute inset-0">
          <div className="absolute bottom-0 left-0 right-[0.49%] top-[36.73%]">
            <svg
              className="block size-full"
              fill="none"
              preserveAspectRatio="none"
              viewBox="0 0 163 104"
            >
              <path d={pieSvgPaths.p10c7800} fill={data[0]?.color || '#F27405'} />
            </svg>
          </div>
        </div>

        {/* Segment 2 - Left side */}
        {data[1] && (
          <div className="absolute inset-0">
            <div className="absolute bottom-[9.33%] left-0 right-[69.97%] top-[36.34%]">
              <svg
                className="block size-full"
                fill="none"
                preserveAspectRatio="none"
                viewBox="0 0 49 89"
              >
                <path d={pieSvgPaths.p2610ab00} fill={data[1].color} />
              </svg>
            </div>
          </div>
        )}

        {/* Segment 3 - Bottom right */}
        {data[2] && (
          <div className="absolute inset-0">
            <div className="absolute bottom-0 left-[5.16%] right-[43.49%] top-[63.77%]">
              <svg
                className="block size-full"
                fill="none"
                preserveAspectRatio="none"
                viewBox="0 0 85 60"
              >
                <path d={pieSvgPaths.p27047a40} fill={data[2].color} />
              </svg>
            </div>
          </div>
        )}

        {/* Segment 4 - Top right */}
        {data[3] && (
          <div className="absolute inset-0">
            <div className="absolute bottom-0 left-[32.71%] right-[13.45%] top-[74.34%]">
              <svg
                className="block size-full"
                fill="none"
                preserveAspectRatio="none"
                viewBox="0 0 89 42"
              >
                <path d={pieSvgPaths.p13733600} fill={data[3].color} />
              </svg>
            </div>
          </div>
        )}

        {/* Center text - total percentage */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl text-muted-foreground">100%</span>
        </div>
      </div>
    </div>
  );
}

export interface LineChartSeries {
  id: string;
  label: string;
  color: string;
  getValue: (item: MonthlyActivity) => number;
}

export interface CustomLineChartProps {
  data: MonthlyActivity[];
  series: LineChartSeries[];
  height?: number;
}

/**
 * Custom Line Chart Component
 *
 * Renders up to three series with smooth SVG lines and labelled axes.
 * Designed for lightweight dashboards without pulling in a charting library.
 */
export function CustomLineChart({
  data,
  series,
  height = 240,
}: CustomLineChartProps) {
  const { t } = useTranslation('charts');

  if (!data || data.length === 0 || !series || series.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-muted-foreground">
        <p>{t('noData')}</p>
      </div>
    );
  }

  const width = 640;
  const padding = { top: 24, right: 24, bottom: 40, left: 48 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const stepX = data.length > 1 ? chartWidth / (data.length - 1) : 0;

  const maxValue = Math.max(
    1,
    ...data.flatMap((month) =>
      series.map((serie) => serie.getValue(month))
    )
  );

  const yTicks = 4;
  const yTickValues = Array.from({ length: yTicks + 1 }, (_, idx) =>
    Math.round((maxValue / yTicks) * idx)
  );

  const pointCoordinates = series.map((serie) => {
    return data.map((month, idx) => {
      const value = serie.getValue(month);
      const x =
        padding.left +
        (data.length > 1 ? idx * stepX : chartWidth / 2);
      const y =
        padding.top +
        (chartHeight - (value / maxValue) * chartHeight);
      return { x, y, value, month: month.name };
    });
  });
  const gridColor = 'hsl(var(--muted))';
  const axisColor = 'hsl(var(--border))';
  const textColor = 'hsl(var(--muted-foreground))';

  return (
    <div className="relative w-full">
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="overflow-visible"
      >
        {/* Grid */}
        {yTickValues.map((value, idx) => {
          const y =
            padding.top +
            (chartHeight - (value / maxValue) * chartHeight);
          return (
            <g key={`tick-${idx}`}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke={idx === 0 ? axisColor : gridColor}
                strokeWidth={idx === 0 ? 1.5 : 1}
                strokeDasharray={idx === 0 ? undefined : '4 4'}
              />
              <text
                x={padding.left - 12}
                y={y + 4}
                textAnchor="end"
                className="text-xs"
                fill={textColor}
              >
                {value}
              </text>
            </g>
          );
        })}

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke={axisColor}
          strokeWidth={1.5}
        />

        {/* Series paths */}
        {pointCoordinates.map((points, serieIdx) => {
          const path = points
            .map((point, idx) =>
              idx === 0
                ? `M ${point.x} ${point.y}`
                : `L ${point.x} ${point.y}`
            )
            .join(' ');
          const serie = series[serieIdx];
          return (
            <g key={serie.id}>
              <path
                d={path}
                fill="none"
                stroke={serie.color}
                strokeWidth={2.4}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {points.map((point, pointIdx) => (
                <circle
                  key={`${serie.id}-point-${pointIdx}`}
                  cx={point.x}
                  cy={point.y}
                  r={4.5}
                  fill={serie.color}
                  className="shadow-sm"
                />
              ))}
            </g>
          );
        })}

        {/* Month labels */}
        {data.map((month, idx) => {
          const x =
            padding.left +
            (data.length > 1
              ? idx * stepX
              : chartWidth / 2);
          return (
            <text
              key={`month-${idx}`}
              x={x}
              y={height - padding.bottom + 24}
              textAnchor="middle"
              className="text-xs"
              fill={textColor}
            >
              {month.name}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

export interface DonutChartDatum {
  name: string;
  value: number;
  color: string;
}

export interface CustomDonutChartProps {
  data: DonutChartDatum[];
  size?: number;
  thickness?: number;
  totalLabel?: string;
}

/**
 * Custom Donut Chart Component
 *
 * Displays proportional slices with stroke-dasharray instead of static SVG paths.
 */
export function CustomDonutChart({
  data,
  size = 170,
  thickness = 22,
  totalLabel,
}: CustomDonutChartProps) {
  const { t } = useTranslation('charts');
  const total = data.reduce((sum, item) => sum + item.value, 0);

  if (!data || data.length === 0 || total === 0) {
    return (
      <div className="flex items-center justify-center h-[200px] text-muted-foreground">
        <p>{t('noDistributionData')}</p>
      </div>
    );
  }

  const center = size / 2;
  const radius = center - thickness / 2;
  const circumference = 2 * Math.PI * radius;
  let cumulative = 0;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="block"
      >
        <circle
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={thickness}
          stroke="hsl(var(--muted))"
          fill="none"
        />

        {data.map((item) => {
          const fraction = item.value / total;
          const segmentLength = fraction * circumference;
          const circle = (
            <circle
              key={item.name}
              cx={center}
              cy={center}
              r={radius}
              stroke={item.color}
              strokeWidth={thickness}
              strokeDasharray={`${segmentLength} ${circumference}`}
              strokeDashoffset={-cumulative}
              fill="none"
              strokeLinecap="round"
              transform={`rotate(-90 ${center} ${center})`}
            />
          );
          cumulative += segmentLength;
          return circle;
        })}
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-xs text-muted-foreground uppercase tracking-wide">
          {totalLabel || t('total')}
        </span>
        <span className="text-2xl font-semibold text-foreground">
          {total}
        </span>
      </div>
    </div>
  );
}

/**
 * Legend component for charts
 */
export interface ChartLegendProps {
  items: {
    name: string;
    color: string;
    percentage: number;
  }[];
}

export function ChartLegend({ items }: ChartLegendProps) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.name} className="flex items-center gap-3">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: item.color }} />
          <span className="text-sm text-card-foreground">{item.name}</span>
          <span className="text-sm text-muted-foreground ml-auto">
            {item.percentage}%
          </span>
        </div>
      ))}
    </div>
  );
}
