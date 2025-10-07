/**
 * Custom Charts Components
 * Migrated from sight/src/components/Dashboard.tsx
 *
 * Provides CustomBarChart and CustomPieChart with dynamic data support
 */

import pieSvgPaths from '@/imports/svg-unlax8gz8c';

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
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-muted-foreground">
        <p>No data available</p>
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
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center w-full h-[200px] text-muted-foreground">
        <p>No data available</p>
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

