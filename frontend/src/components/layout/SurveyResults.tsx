import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Download, Users, TrendingUp, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { surveysApi } from '@/lib/api';
import type { Survey } from '@/types';

interface SurveyResultsProps {
  survey: Survey;
  onBack: () => void;
}

export function SurveyResults({ survey, onBack }: SurveyResultsProps) {
  const { data: results, isLoading } = useQuery({
    queryKey: ['survey-results', survey.id],
    queryFn: () => surveysApi.getResults(survey.id),
    enabled: survey.status === 'completed',
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading results...</p>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">No results available</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-foreground">{results.title}</h1>
            <p className="text-muted-foreground">Survey Results & Analytics</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Responses</p>
                <p className="text-2xl brand-orange">{results.actual_responses.toLocaleString()}</p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completion Rate</p>
                <p className="text-2xl brand-orange">{Math.round(results.completion_rate)}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg. Response Time</p>
                <p className="text-2xl brand-orange">
                  {results.average_response_time_ms
                    ? `${(results.average_response_time_ms / 1000).toFixed(1)}s`
                    : 'N/A'}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results Tabs */}
      <Tabs defaultValue="questions" className="space-y-6">
        <TabsList className="bg-muted border border-border">
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
        </TabsList>

        <TabsContent value="questions" className="space-y-6">
          {results.question_analytics.map((qa, index) => (
            <Card key={qa.question_id} className="bg-card border border-border">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">Q{index + 1}</Badge>
                      <Badge className="bg-primary/10 text-primary">{qa.question_type}</Badge>
                    </div>
                    <CardTitle className="text-lg text-card-foreground">{qa.question_title}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {qa.responses_count} responses
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* Single Choice / Multiple Choice - Bar Chart */}
                {(qa.question_type === 'single-choice' || qa.question_type === 'multiple-choice') && qa.statistics.distribution && (
                  <div className="space-y-4">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={Object.entries(qa.statistics.distribution).map(([name, value]) => ({
                          name,
                          value: value as number,
                        }))}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
                        <YAxis stroke="hsl(var(--muted-foreground))" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                          }}
                        />
                        <Bar dataKey="value" fill="#F27405" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                    {qa.statistics.most_common && (
                      <p className="text-sm text-muted-foreground">
                        Most popular: <span className="text-card-foreground font-medium">{qa.statistics.most_common}</span>
                      </p>
                    )}
                  </div>
                )}

                {/* Rating Scale - Stats */}
                {qa.question_type === 'rating-scale' && qa.statistics.mean !== undefined && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="text-center">
                        <p className="text-2xl brand-orange">{qa.statistics.mean.toFixed(2)}</p>
                        <p className="text-xs text-muted-foreground">Mean</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl text-card-foreground">{qa.statistics.median}</p>
                        <p className="text-xs text-muted-foreground">Median</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl text-card-foreground">{qa.statistics.mode}</p>
                        <p className="text-xs text-muted-foreground">Mode</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl text-card-foreground">{qa.statistics.min}</p>
                        <p className="text-xs text-muted-foreground">Min</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl text-card-foreground">{qa.statistics.max}</p>
                        <p className="text-xs text-muted-foreground">Max</p>
                      </div>
                    </div>
                    {qa.statistics.distribution && (
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart
                          data={Object.entries(qa.statistics.distribution).map(([rating, count]) => ({
                            rating,
                            count: count as number,
                          }))}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                          <XAxis dataKey="rating" stroke="hsl(var(--muted-foreground))" />
                          <YAxis stroke="hsl(var(--muted-foreground))" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--card))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                          />
                          <Bar dataKey="count" fill="#F29F05" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                )}

                {/* Open Text - Sample Responses */}
                {qa.question_type === 'open-text' && qa.statistics.sample_responses && (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Avg. {qa.statistics.avg_word_count?.toFixed(1)} words per response
                    </p>
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-card-foreground">Sample Responses:</p>
                      {qa.statistics.sample_responses.slice(0, 3).map((response: string, idx: number) => (
                        <div key={idx} className="p-3 bg-muted/30 rounded-lg border border-border">
                          <p className="text-sm text-card-foreground italic">&ldquo;{response}&rdquo;</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="demographics" className="space-y-6">
          {/* Demographics Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(results.demographic_breakdown).map(([category, data]) => (
              <Card key={category} className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-card-foreground capitalize">
                    {category.replace('by_', '').replace('_', ' ')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(data).map(([segment, info]: [string, any]) => (
                      <div key={segment} className="flex items-center justify-between">
                        <span className="text-sm text-card-foreground">{segment}</span>
                        <span className="text-sm text-muted-foreground">{info.count} responses</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
