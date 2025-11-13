import { useState } from 'react';
import { useSurveyResults } from '@/hooks/surveys/useSurveyResults';
import type { QuestionAnalytics } from '@/types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { FileText, Users, TrendingUp, Clock, AlertCircle } from 'lucide-react';

interface SurveyResultsProps {
  surveyId: string;
}

// Kolory dla wykresów
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

// Sub-komponenty wizualizacji
interface RatingScaleChartProps {
  distribution: Record<string, number>;
  stats: QuestionAnalytics['stats'];
}

function RatingScaleChart({ distribution, stats }: RatingScaleChartProps) {
  const data = Object.entries(distribution)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([rating, count]) => ({
      rating: `${rating}`,
      count,
    }));

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="rating"
            label={{ value: 'Ocena', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            label={{ value: 'Liczba odpowiedzi', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#3b82f6" name="Liczba odpowiedzi" />
        </BarChart>
      </ResponsiveContainer>

      {stats && (
        <div className="grid grid-cols-5 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.mean.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">Średnia</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.median.toFixed(1)}</div>
            <div className="text-xs text-muted-foreground">Mediana</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.std_dev.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">Odchylenie</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.min}</div>
            <div className="text-xs text-muted-foreground">Min</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.max}</div>
            <div className="text-xs text-muted-foreground">Max</div>
          </div>
        </div>
      )}
    </div>
  );
}

interface ChoiceChartProps {
  distribution: Record<string, number>;
  questionType: QuestionAnalytics['question_type'];
}

function ChoiceChart({ distribution }: ChoiceChartProps) {
  const data = Object.entries(distribution).map(([option, count]) => ({
    name: option,
    value: count,
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry) => `${entry.name}: ${((entry.value / total) * 100).toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((_entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>

      <div className="space-y-2">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between border-b pb-2">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <span className="text-sm">{item.name}</span>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium">{item.value}</div>
              <div className="text-xs text-muted-foreground">
                {((item.value / total) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface DemographicChartProps {
  data: Record<string, { count: number; avg_rating: number }>;
  label: string;
}

function DemographicChart({ data, label }: DemographicChartProps) {
  const chartData = Object.entries(data).map(([key, value]) => ({
    name: key,
    count: value.count,
    avg_rating: value.avg_rating,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="name"
          label={{ value: label, position: 'insideBottom', offset: -5 }}
        />
        <YAxis
          yAxisId="left"
          label={{ value: 'Liczba person', angle: -90, position: 'insideLeft' }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          label={{ value: 'Średnia ocena', angle: 90, position: 'insideRight' }}
        />
        <Tooltip />
        <Legend />
        <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Liczba person" />
        <Bar yAxisId="right" dataKey="avg_rating" fill="#10b981" name="Średnia ocena" />
      </BarChart>
    </ResponsiveContainer>
  );
}

function SurveyResultsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

function SurveyResultsError({ error }: { error: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertCircle className="w-5 h-5" />
          Błąd ładowania wyników
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {error?.message || 'Nie udało się załadować wyników ankiety'}
        </p>
      </CardContent>
    </Card>
  );
}

export function SurveyResults({ surveyId }: SurveyResultsProps) {
  const { data: results, isLoading, error } = useSurveyResults(surveyId);
  const [selectedQuestionIndex, setSelectedQuestionIndex] = useState(0);

  if (isLoading) {
    return <SurveyResultsSkeleton />;
  }

  if (error || !results) {
    return <SurveyResultsError error={error} />;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(results.completion_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {results.responding_personas} / {results.total_personas} person
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Responses</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{results.responding_personas}</div>
            <p className="text-xs text-muted-foreground">persony odpowiedziały</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Questions</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{results.question_analytics.length}</div>
            <p className="text-xs text-muted-foreground">pytań w ankiecie</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(results.average_response_time_ms / 1000).toFixed(1)}s
            </div>
            <p className="text-xs text-muted-foreground">per persona</p>
          </CardContent>
        </Card>
      </div>

      {/* Question Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Wyniki Pytań</CardTitle>
          <CardDescription>
            Kliknij pytanie aby zobaczyć szczegółową wizualizację
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={selectedQuestionIndex.toString()} onValueChange={(v) => setSelectedQuestionIndex(parseInt(v))}>
            <TabsList className="flex-wrap h-auto">
              {results.question_analytics.map((q, index) => (
                <TabsTrigger key={q.question_id} value={index.toString()}>
                  Pytanie {index + 1}
                </TabsTrigger>
              ))}
            </TabsList>

            {results.question_analytics.map((q, index) => (
              <TabsContent key={q.question_id} value={index.toString()} className="space-y-4">
                <div>
                  <h3 className="text-lg font-medium">{q.question_text}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline">{q.question_type}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {q.total_responses} responses ({(q.response_rate * 100).toFixed(1)}%)
                    </span>
                  </div>
                </div>

                {/* Visualization */}
                {q.question_type === 'rating_scale' && (
                  <RatingScaleChart distribution={q.distribution} stats={q.stats} />
                )}
                {(q.question_type === 'single_choice' || q.question_type === 'multiple_choice') && (
                  <ChoiceChart distribution={q.distribution} questionType={q.question_type} />
                )}
                {q.question_type === 'open_text' && (
                  <div className="p-4 border rounded-figma-inner bg-muted/50">
                    <p className="text-sm text-muted-foreground">
                      Odpowiedzi otwarte - wkrótce word cloud
                    </p>
                  </div>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Demographic Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Analiza Demograficzna</CardTitle>
          <CardDescription>
            Podział wyników według wieku, płci i wykształcenia
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="age">
            <TabsList>
              <TabsTrigger value="age">Wiek</TabsTrigger>
              <TabsTrigger value="gender">Płeć</TabsTrigger>
              <TabsTrigger value="education">Wykształcenie</TabsTrigger>
            </TabsList>

            <TabsContent value="age">
              <DemographicChart data={results.demographic_breakdown.by_age} label="Grupa wiekowa" />
            </TabsContent>
            <TabsContent value="gender">
              <DemographicChart data={results.demographic_breakdown.by_gender} label="Płeć" />
            </TabsContent>
            <TabsContent value="education">
              <DemographicChart data={results.demographic_breakdown.by_education} label="Wykształcenie" />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
